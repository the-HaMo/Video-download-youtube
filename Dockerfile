# Usamos una versión ligera de Python
FROM python:3.11-slim

# Instalamos FFmpeg en el sistema operativo del contenedor
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Creamos la carpeta de trabajo
WORKDIR /app

# Copiamos las dependencias y las instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo nuestro código
COPY . .

# Comando maestro para encender la web usando el puerto que la nube nos asigne
CMD gunicorn -b 0.0.0.0:$PORT app:app