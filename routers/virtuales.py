from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

## Importar modelos de las BD
import BD.models as models
import BD.database as database 
import schemas.schemas as schemas
from BD.database import get_db

router = APIRouter()

#-------------------------#
#---- ENDPOINTS - GET ----#
#-------------------------#

@router.get("/virtuales/radares")
async def datos_virtuales(db: Session = Depends(get_db)):
    virtual = db.query(models.Virtual).all()
    return virtual

#--------------------------#
#---- ENDPOINTS - POST ----#
#--------------------------#

@router.post("/create/radar_virtual")
async def create_virtual(virtual: schemas.Virtuales, db: Session = Depends(get_db)):
    db_virtual = models.Virtual(
        nombre=virtual.nombre,
        id_vinculacion=virtual.id_vinculacion,
        volumen=virtual.volumen,
        umbral=virtual.umbral,
        combustible=virtual.combustible,
        vinculacion=virtual.vinculacion
    )
    db.add(db_virtual)
    db.commit()
    db.refresh(db_virtual)
    return {"Creación de dispositvo virtual exitosa"}

#-------------------------#
#---- ENDPOINTS - PUT ----#
#-------------------------#

@router.put("/virtuales/{id_registro}")
def update_radar_virtual(id_registro: int, virtual: schemas.VirtualUpdate, db: Session = Depends(get_db)):
    # Buscar el radar a actualizar
    db_virtual = db.query(models.Virtual).filter(models.Virtual.id_registro == id_registro).first()
    if db_virtual is None:
        return {"error": f"No se encontró el radar virual con id {id_registro}"}
    
    # Actualizar campos
    db_virtual.nombre = virtual.nombre
    db_virtual.volumen = virtual.volumen
    db_virtual.umbral = virtual.umbral

    db.add(db_virtual)
    db.commit()
    db.refresh(db_virtual)



#----------------------------#
#---- ENDPOINTS - DELETE ----#
#----------------------------#

@router.delete("/virtuales/{id_registro}")
def delete_virtual(id_registro: int, db: Session = Depends(get_db)):
    db_radar = db.query(models.Virtual).filter(models.Virtual.id_registro == id_registro).first()
    if db_radar is None:
        raise HTTPException(status_code=404, detail=f"No se encontró el radar con la id {id_registro}")
    db.delete(db_radar)
    db.commit()
    return


