from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from BD.database import  engine
import BD.models as models
from fastapi.middleware.cors import CORSMiddleware
import logging
from routers import radares, virtuales, websocket
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
        # Registrar error
        return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})

## LLAMADAS WEBSOCKET

## LLAMADAS API
#@app.get("/radares/")
#async def get_radares(db: Session = Depends(get_db)):
#    radares = db.query(models.Radar).all()
#    return radares

#@app.get("/grafico_datos/{id_radar}")
#async def get_datos(id_radar: str, db: Session = Depends(get_db)):
#    datos = db.query(models.HistorialRadar).filter(models.HistorialRadar.id_radar == id_radar).all()
#    return datos

# Endpoint para obtener todos los sensores
#@app.get("/radares/graficos2")
#def obtener_radares(db: Session = Depends(get_db)):
    # Obtener los datos de los sensores
    #radar = db.query(models.HistorialRadar).all()

    # Extraer los datos de combustible y tiempo
    #combustible = [sensor.combustible for sensor in radar]
    #tiempo = [sensor.fecha for sensor in radar]
    # Crear el gráfico
    #plt.figure(figsize=(10, 6))
    #plt.plot(tiempo, combustible, marker='o', linestyle='-', color='b')
    #plt.title('Combustible vs Tiempo')
    #plt.xlabel('Tiempo')
    #plt.ylabel('Combustible')
    #plt.grid(True)

    # Guardar el gráfico en un buffer
    #buf = io.BytesIO()
    #plt.savefig(buf, format='png')
    #plt.close()
    #buf.seek(0)

    # Devolver la imagen como respuesta
    #return Response(content=buf.getvalue(), media_type="image/png")




