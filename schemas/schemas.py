from pydantic import BaseModel
from typing import Optional, List

class HistorialRadarResponse(BaseModel):
    id_radar: str
    combustible: float
    estado: bool
    #fecha: datetime

    class Config:
        from_attributes = True  # Habilita la compatibilidad con ORM

# Esquema para Radar
class RadarResponse(BaseModel):
    id_radar: str
    nombre: Optional[str]   # Nuevo campo
    volumen: Optional[float]  # Nuevo campo
    umbral: Optional[float]
    historico: List[HistorialRadarResponse]
    class Config:
        from_attributes = True  # Habilita la compatibilidad con ORM

class HistorialRadarRequest(BaseModel):
    id_radar: str
    combustible: float
    estado: bool
    #fecha: datetime

class RadarRequest(BaseModel):
    id_radar: str
    historico: HistorialRadarRequest

#
class SensorSchema(BaseModel):
    combustible: float
    estado: bool

class EstadoUpdate(BaseModel):
    estado: bool

class RadarUpdate(BaseModel):
    id_radar: str
    nombre: Optional[str] = None
    volumen: Optional[float] = None
    umbral: Optional[float] = None

class Virtuales(BaseModel):
    nombre: str
    id_vinculacion : Optional[str] = None
    volumen : float
    umbral: float
    combustible : float = 0.0
    vinculacion : bool = False

class VirtualUpdate(BaseModel):
    id_registro: int
    nombre: Optional[str] = None
    volumen: Optional[float] = None
    umbral: Optional[float] = None