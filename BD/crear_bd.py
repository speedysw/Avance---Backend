import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import os 

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
load_dotenv(dotenv_path)

def create_bd():
    dbname = os.getenv("DATABASE_NAME")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASS")
    host = os.getenv("DATABASE_HOST_LOCAL", "localhost")
    port = os.getenv("DATABASE_PORT", "5432")

    try:
        # Conectarse al servidor sin especificar base de datos
        conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Permitir CREATE DATABASE

        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f'CREATE DATABASE "{dbname}"')
            print(f"Base de datos '{dbname}' creada exitosamente.")
        else:
            print(f"ℹLa base de datos '{dbname}' ya existe.")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error al crear la base de datos: {e}")
