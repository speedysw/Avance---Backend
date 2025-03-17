from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from BD.database import  engine
import BD.models as models
from fastapi.middleware.cors import CORSMiddleware
import logging
from routers import radares, virtuales, websocket, autenticacion
from services_mqtt import init_mqtt

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos 
    allow_headers=["*"],  # Permitir todos los encabezados
)

models.Base.metadata.create_all(bind=engine)

app.include_router(radares.router)
app.include_router(virtuales.router)
app.include_router(websocket.router)
app.include_router(autenticacion.router)

# Iniciar la conexión MQTT en el evento startup para que no bloquee el arranque de la API
@app.on_event("startup")
async def startup_event():
    init_mqtt()

@app.get("/")
def leer_raiz():
    
    return {
        "mensaje":"Bienvenido a la aplicacion",
    }

@app.middleware("http")
async def global_exception_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": "Error interno del servidor"},
            headers={"Access-Control-Allow-Origin": "*"}  # Agrega la cabecera de CORS
        )

