from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
from fastapi import HTTPException
from contextlib import contextmanager
from dotenv import load_dotenv
import os 
from BD.crear_bd import create_bd

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
load_dotenv(dotenv_path)
host = os.getenv("DATABASE_HOST_LOCAL")
port = os.getenv("DATABASE_PORT")
user = os.getenv("DATABASE_USER")
password = os.getenv("DATABASE_PASS")
database = os.getenv("DATABASE_NAME")

create_bd()
SQL_DB_URL =  f"postgresql://{user}:{password}@{host}:{port}/{database}"
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