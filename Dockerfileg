# Usa una imagen base de Python
FROM python:3.9-slim

# Configurar el entorno de trabajo
WORKDIR /app

# Instalar ffmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copiar los archivos necesarios
COPY . /app

# Instalar las dependencias
RUN pip install --no-cache-dir pyrogram ffmpeg-python tgcrypto pydub gradio flask

# Crear el directorio de sesiones
RUN mkdir -p /app/session

# Establecer permisos correctos
RUN chown -R 1000:1000 /app

# Iniciar el bot
USER 1000
CMD ["python", "main.py"]
