FROM python:3.10-slim

# Instalar dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev

WORKDIR /app

# Copiar el archivo de requerimientos
COPY ./requirements.txt /app/requirements.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copiar el resto de los archivos de la aplicación
COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
