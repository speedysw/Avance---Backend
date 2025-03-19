from BD.database import Base
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, String, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship

class Radar(Base):
    __tablename__ = "radar"
    id_radar = Column(String(255), primary_key=True)
    nombre = Column(String(100), nullable=True)
    volumen = Column(Float, nullable=True) 
    umbral = Column(Float, nullable=True)
    duration = Column(Integer, nullable=True)
    timerActive = Column(Boolean, nullable=True)
    hora_termino = Column(DateTime(timezone=True), nullable=False)

    # Relación con RadarHistorico
    historico = relationship("HistorialRadar", back_populates="radar", cascade="all, delete") 

class HistorialRadar(Base):
    __tablename__ = "historial_radar"
    id_consulta = Column(Integer, primary_key=True, autoincrement=True)
    id_radar = Column(String(255), ForeignKey('radar.id_radar', ondelete="CASCADE"), nullable=False)
    combustible = Column(Float)
    estado = Column(Boolean)
    fecha = Column(DateTime, default=datetime.utcnow)
    # Relación con Radar
    radar = relationship("Radar", back_populates="historico")  # Relación con la clase Radar

class Virtual(Base):
    __tablename__= "dispositivos_virtuales"
    id_registro = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=True)
    id_vinculacion = Column(String(255), nullable=True)
    volumen = Column(Float, nullable=True) 
    umbral = Column(Float, nullable=True)
    combustible = Column(Float)
    vinculacion = Column(Boolean)

class User(Base):
    __tablename__="usuario"
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100))
    nombre = Column(String(100))
    password = Column(String(100))
    rol = Column(Integer, default=0)