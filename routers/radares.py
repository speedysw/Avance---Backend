from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

## Importar funciones
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import json
from io import StringIO
import pandas as pd


## Importar modelos de las BD
import BD.models as models
import schemas.schemas as schemas
from BD.database import get_db, get_columns
from .autenticacion import get_current_user, require_role

## Funciones MQTT
from services_mqtt import publish_message, MQTT_TOPIC_CONTROL_BASE 

router = APIRouter()

#-------------------------#
#---- ENDPOINTS - GET ----#
#-------------------------#

@router.get("/columns/{table_name}", response_model=List[str])
async def get_columns_from_table(table_name: str):
    columns = get_columns(table_name)
    if not columns:
        raise HTTPException(status_code=404, detail="Tabla no encontrada o sin columnas")
    return columns

@router.get("/get_datos")
async def get_datos(radar: Optional[str], estado: Optional[str], fecha_registro: Optional[str], db: Session = Depends(get_db)):
    query = db.query(models.HistorialRadar)

    if estado == "Encendido":
        query = query.filter(models.HistorialRadar.estado == True)
    elif estado == "Apagado":
        query = query.filter(models.HistorialRadar.estado == False)

    if radar:
        query = query.filter(models.HistorialRadar.id_radar == radar)

    if fecha_registro:
        fecha_registro = datetime.strptime(fecha_registro, "%Y-%m-%d")
        query = query.filter(func.date(models.HistorialRadar.fecha) == fecha_registro)

    datos = query.all()
    return datos

@router.get("/radares/last_date")
async def datos_radares(db: Session = Depends(get_db)):
    subquery = (
        db.query(
            models.HistorialRadar.id_radar,
            func.max(models.HistorialRadar.fecha).label("max_fecha")
        )
        .group_by(models.HistorialRadar.id_radar)
        .subquery()
    )

    ultimos_sensores = (
        db.query(models.HistorialRadar)
        .join(
            subquery,
            (models.HistorialRadar.id_radar == subquery.c.id_radar)
            & (models.HistorialRadar.fecha == subquery.c.max_fecha),
        )
        .join(models.HistorialRadar.radar)
        .order_by(models.HistorialRadar.id_radar)  # Ordena por id_radar
        .all()
    )

    return [
        {
            "id_radar": sensor.id_radar,
            "combustible": sensor.combustible,
            "estado": sensor.estado,
            "fecha": sensor.fecha.isoformat() if sensor.fecha else None,
            # Usar la relación radar:
            "nombre": sensor.radar.nombre,
            "volumen": sensor.radar.volumen,
            "umbral": sensor.radar.umbral
        }
        for sensor in ultimos_sensores
    ]

@router.get("/radar/{id}/last_date")
def ultimos_datos_por_radar(id_radar: str ,db: Session = Depends(get_db)):
    db_radar = db.query(models.HistorialRadar).filter(models.HistorialRadar.id_radar == id_radar).order_by(models.HistorialRadar.fecha.desc()).first()
    if db_radar is None:
        return {"error": f"No se encontraron datos para el radar {id_radar}"}
    return db_radar

@router.get("/get_datos_by_range")
async def get_datos_by_range(
    radar: str,
    fecha_inicio: Optional[str] = None,
    fecha_final: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.HistorialRadar).filter(models.HistorialRadar.id_radar == radar)

    if fecha_inicio and fecha_final:
        try:
            start_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            end_dt = datetime.strptime(fecha_final, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return {"error": "El formato de las fechas debe ser YYYY-MM-DD"}

        query = query.filter(
            and_(
                models.HistorialRadar.fecha >= start_dt,
                models.HistorialRadar.fecha < end_dt
            )
        )

    datos = query.all()
    return datos

@router.get("/datos/radares")
async def datos_radares(db: Session = Depends(get_db)):
    datos = db.query(models.Radar)
    subquery = (
        db.query(
            models.HistorialRadar.id_radar,
            func.min(models.HistorialRadar.fecha).label("min_fecha")
        )
        .group_by(models.HistorialRadar.id_radar)
        .subquery()
    )
    ultimos_sensores = (
        db.query(models.HistorialRadar)
        .join(
            subquery,
            (models.HistorialRadar.id_radar == subquery.c.id_radar)
            & (models.HistorialRadar.fecha == subquery.c.min_fecha),
        )
        .join(models.HistorialRadar.radar)
        .all()
    )   

    return [
        {
            "id_radar": sensor.id_radar,
            "nombre": sensor.radar.nombre,
            "volumen": sensor.radar.volumen,
            "umbral": sensor.radar.umbral,
            "fecha": sensor.fecha.isoformat() if sensor.fecha else None,
        }
        for sensor in ultimos_sensores
    ]

@router.get("/export/csv")
async def exportar_csv(radar: str,fecha_inicio: Optional[str] = None,fecha_final: Optional[str] = None,db: Session = Depends(get_db)):
    query = db.query(models.HistorialRadar).filter(models.HistorialRadar.id_radar == radar)

    if fecha_inicio and fecha_final:
        try:
            start_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            end_dt = datetime.strptime(fecha_final, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return {"error": "El formato de las fechas debe ser YYYY-MM-DD"}

        query = query.filter(
            and_(
                models.HistorialRadar.fecha >= start_dt,
                models.HistorialRadar.fecha < end_dt
            )
        )

    datos = query.all()
    datos = query.all()
    data_list = [d.__dict__ for d in datos]
    # Eliminar atributos internos (como _sa_instance_state)
    for item in data_list:
        item.pop("_sa_instance_state", None)
    df = pd.DataFrame(data_list)

    
    # Escribir en un objeto BytesIO
    csv_stream = StringIO()
    df.to_csv(csv_stream, index=False)
    response = Response(content=csv_stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=datos.csv"
    return response



#--------------------------#
#---- ENDPOINTS - POST ----#
#--------------------------#


@router.post("/agregar_radares")
async def create_radar(radar: schemas.RadarRequest, db: Session = Depends(get_db),  current_user: models.User = Depends(require_role(1))):

    # Verifica si el radar ya existe
    db_radar = db.query(models.Radar).filter(models.Radar.id_radar == radar.id_radar).first()
    if not db_radar:
        # Si el Radar no existe, se busca un dispositivo virtual pendiente de vinculación
        pendiente_virtual = db.query(models.Virtual).filter(models.Virtual.vinculacion == False).first()
        
        if pendiente_virtual:
            # Toma los valores del dispositivo virtual pendiente
            new_nombre = pendiente_virtual.nombre
            new_volumen = pendiente_virtual.volumen
            new_umbral = pendiente_virtual.umbral
            
            # Actualiza el dispositivo virtual para vincularlo con el nuevo Radar
            pendiente_virtual.id_vinculacion = radar.id_radar
            pendiente_virtual.vinculacion = True
            db.add(pendiente_virtual)
            db.commit()
        else:
            # Si no hay dispositivo virtual pendiente, se usan valores por defecto o los que vienen en la petición
            new_nombre = "Default Radar"
            new_volumen = 100.0  # Valor por defecto
            new_umbral = 0.0
        
        # Crea el nuevo Radar utilizando los valores determinados
        db_radar = models.Radar(
            id_radar=radar.id_radar,
            nombre=new_nombre,
            volumen=new_volumen,
            umbral=new_umbral
        )
        db.add(db_radar)
        db.commit()
        db.refresh(db_radar)
    
    # Crea un nuevo registro de historial
    db_historial = models.HistorialRadar(
        id_radar=radar.historico.id_radar,
        combustible=radar.historico.combustible,
        estado=radar.historico.estado,
        fecha=datetime.now(),
    )
    db.add(db_historial)
    
    # Confirma los cambios en la base de datos
    db.commit()
    db.refresh(db_radar)
    
    # Retorna la respuesta con el radar y su historial
    return db_radar

@router.post("/switch/{id_radar}")
async def change_switch(id_radar: str, data: schemas.EstadoUpdate, db: Session = Depends(get_db)):

    # Buscar el último estado del radar en la BD
    db_radar = (
        db.query(models.HistorialRadar)
        .filter(models.HistorialRadar.id_radar == id_radar)
        .order_by(models.HistorialRadar.fecha.desc())
        .first()
    )

    if db_radar is None:
        
        return {"error": f"No se encontraron datos para el radar {id_radar}"}
    nuevo_historial = models.HistorialRadar(
        id_radar=id_radar,
        combustible=db_radar.combustible,  # o algún valor si es necesario
        estado=data.estado,
        fecha=datetime.now()
    )
    db.add(nuevo_historial)
    db.commit()
    db.refresh(nuevo_historial)
    # Preparar mensaje MQTT
    payload = json.dumps({"id_sensor": id_radar, "estado": data.estado})

    # Construir el tópico de forma dinámica
    topic = MQTT_TOPIC_CONTROL_BASE + "/" + id_radar
    print(topic)
    try:
        # Publicar mensaje en el tópico MQTT exclusivo para el radar
        publish_message(topic, payload)
        return {
            "message": "Switch changed",
            "estado": db_radar.estado,
            "mqtt_payload": payload,
            "topic": topic
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar mensaje MQTT: {str(e)}"
        )
    
#-------------------------#
#---- ENDPOINTS - PUT ----#
#-------------------------#

@router.put("/radares/{id_radar}")
async def update_radar(id_radar: str, radar: schemas.RadarUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(1))):
    # Buscar el radar a actualizar
    db_radar = db.query(models.Radar).filter(models.Radar.id_radar == id_radar).first()
    if db_radar is None:
        raise HTTPException(status_code=404, detail=f"No se encontró el radar con id {id_radar}")
    
    # Actualizar campos del radar físico
    db_radar.nombre = radar.nombre
    db_radar.volumen = radar.volumen
    db_radar.umbral = radar.umbral
    db.add(db_radar)
    db.commit()
    db.refresh(db_radar)

    # Buscar el radar virtual relacionado (si existe)
    db_virtual = db.query(models.Virtual).filter(models.Virtual.id_vinculacion == id_radar).first()
    if db_virtual:
        db_virtual.nombre = radar.nombre
        db_virtual.volumen = radar.volumen
        db_virtual.umbral = radar.umbral
        db.add(db_virtual)
        db.commit()
        db.refresh(db_virtual)

    # Realizar el join para obtener datos del historial asociado.
    result = db.query(models.Radar, models.HistorialRadar).join(
        models.HistorialRadar, models.Radar.id_radar == models.HistorialRadar.id_radar
    ).filter(models.Radar.id_radar == id_radar).order_by(models.HistorialRadar.fecha.desc()).first()

    if result:
        radar_db, historial = result
        response_data = {
            "id_radar": radar_db.id_radar,
            "nombre": radar_db.nombre,
            "volumen": radar_db.volumen,
            "umbral": radar_db.umbral,
            "combustible": historial.combustible,
            "estado": historial.estado,
            "fecha": historial.fecha.isoformat() if historial.fecha else None
        }
    else:
        response_data = {
            "id_radar": db_radar.id_radar,
            "nombre": db_radar.nombre,
            "volumen": db_radar.volumen,
            "umbral": db_radar.umbral,
            "combustible": None,
            "estado": None,
            "fecha": None
        }
    
    return response_data

#----------------------------#
#---- ENDPOINTS - DELETE ----#
#----------------------------#

@router.delete("/radares/{id_radar}", status_code=status.HTTP_204_NO_CONTENT)
def delete_radar(id_radar: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_role(1))):
    print(f"Intentando borrar radar: {id_radar}")
    db_radar = db.query(models.Radar).filter(models.Radar.id_radar == id_radar).first()
    print(f"Resultado de búsqueda: {db_radar}")
    if db_radar is None:
        raise HTTPException(status_code=404, detail=f"No se encontró el radar con id {id_radar}")

    # Eliminar la entrada en Virtual
    db.query(models.Virtual).filter(models.Virtual.id_vinculacion == id_radar).delete()
    
    # Eliminar el radar
    db.delete(db_radar)
    db.commit()
    return
