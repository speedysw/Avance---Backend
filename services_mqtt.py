# app/mqtt_client.py
import BD.models as models
from datetime import datetime
from BD.database import SessionLocal
import logging, json
import paho.mqtt.client as mqtt
from pydantic import BaseModel, ValidationError

class MQTTMessage(BaseModel):
    id_sensor: str
    combustible: float
    estado: bool

logger = logging.getLogger(__name__)

MQTT_BROKER = "192.168.0.110"
MQTT_PORT = 1883
MQTT_TOPIC_CONTROL_BASE = "generador/control"
MQTT_TOPIC_COMBUSTIBLE = "generador/combustible"

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    logger.info("Conectado a MQTT con código %s", rc)
    client.subscribe(MQTT_TOPIC_COMBUSTIBLE)

def on_message(client, userdata, msg):
    try:
        data = msg.payload.decode()
        try:
            payload = MQTTMessage.parse_raw(data)
        except ValidationError as ve:
            logger.error("Mensaje MQTT inválido: %s", ve)
            return

        logger.info("Mensaje recibido en %s: %s", msg.topic, payload.dict())
        process_message(payload)
    except Exception as e:
        logger.error("Error procesando mensaje MQTT: %s", e)

# Asignar funciones de callback al cliente MQTT

def process_message(payload: MQTTMessage):
    db = SessionLocal()
    try:
        db_radar = db.query(models.Radar).filter(models.Radar.id_radar == payload.id_sensor).first()
        if not db_radar:
            pendiente_virtual = (
                db.query(models.Virtual)
                .filter(models.Virtual.vinculacion == False)
                .order_by(models.Virtual.id_registro.asc())
                .first()
            )
            if pendiente_virtual:
                new_nombre = pendiente_virtual.nombre
                new_volumen = pendiente_virtual.volumen
                new_umbral = pendiente_virtual.umbral
                pendiente_virtual.id_vinculacion = payload.id_sensor
                pendiente_virtual.vinculacion = True
                db.add(pendiente_virtual)
                db.commit()
            else:
                new_nombre = "Default Radar"
                new_volumen = 100.0
                new_umbral = 0.0
                new_duration = 0
                new_timerActive = False 
            db_radar = models.Radar(
                id_radar=payload.id_sensor,
                nombre=new_nombre,
                volumen=new_volumen,
                umbral=new_umbral,
                duration=new_duration,
                timerActive=new_timerActive
                
            )
            db.add(db_radar)
            db.commit()
            db.refresh(db_radar)

        db_historial = models.HistorialRadar(
            id_radar=payload.id_sensor,
            combustible=payload.combustible,
            estado=payload.estado,
            fecha=datetime.now(),
        )
        db.add(db_historial)
        db.commit()
        logger.info("Datos guardados en la base de datos para el sensor %s", payload.id_sensor)
    except Exception as e:
        logger.error("Error al guardar en la base de datos: %s", e)
        db.rollback()
    finally:
        db.close()
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbCI6MSwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc0MjIzNDgzNH0.HmlIuNk7YEqmBHB_qZhMPl_r4Mczqd9SCxKYXOWngUw
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbCI6MSwidHlwZSI6ImFjY2VzcyIsImV4cCI6MTc0MjIzNTMyMn0.AQnCyZbiAcnKrF1bOn9MuYjOp2vY4DSAGr175ymX4oA
def init_mqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()  # Inicia el loop en un hilo separado
        logger.info("Conexión MQTT establecida y loop iniciado.")
    except Exception as e:
        logger.error("Error al conectar a MQTT: %s", e)

def publish_message(topic: str, payload: str):
    try:
        # Intenta decodificar el payload para asegurarte de que es un JSON válido
        json.loads(payload)
    except json.JSONDecodeError as e:
        logger.error("Payload no es un JSON válido: %s", e)
        raise Exception("Payload no es un JSON válido")
    
    result = mqtt_client.publish(topic, payload)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        logger.error("Error al publicar mensaje en MQTT, código: %s", result.rc)
        raise Exception(f"Error al publicar mensaje en MQTT, código: {result.rc}")

