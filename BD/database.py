from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
from fastapi import HTTPException
from contextlib import contextmanager


SQL_DB_URL = 'postgresql://postgres:rollins12@localhost:5432/Prueba'
engine = create_engine(SQL_DB_URL)
SessionLocal = sessionmaker(bind=engine,autocommit=False,autoflush=False)
Base = declarative_base()

def get_columns(table_name: str) -> List[str]:
    # Inspeccionamos la base de datos para obtener las columnas de la tabla
    inspector = inspect(engine)
    try:
        columns = [column["name"] for column in inspector.get_columns(table_name)]
        return columns[1:]
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error al consultar la tabla: {str(e)}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()