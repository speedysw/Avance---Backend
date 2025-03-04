# Imagen basada en Python
FROM python:3.9-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos necesarios
COPY ./requirements.txt /app/requirements.txt

# Instalar dependencias
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copiar el resto de los archivos
COPY . .

# Documentar el puerto que se utilizará
EXPOSE 8000

# CMD
CMD uvicorn app:app --host 0.0.0.0 --port 8000
