from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from BD.database import get_db
import BD.models as models
from sqlalchemy import func
import json
import asyncio

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        while True:
            print("Cliente Conectado")
            # Simular la actualización de datos de un sensor cada 5 segundos
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
                .join(models.HistorialRadar.radar)  # para cargar la relación 'radar'
                .all()
            )

            cadena_datos = [
                {
                    "id_radar": sensor.id_radar,
                    "combustible": sensor.combustible,
                    "nombre": sensor.radar.nombre,
                    "umbral": sensor.radar.umbral
                }
                for sensor in ultimos_sensores
            ]
            await websocket.send_text(json.dumps(cadena_datos))
            await asyncio.sleep(10)
    
    except WebSocketDisconnect:
        print("Cliente desconectado")
