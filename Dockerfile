# ---------------------------
# Etapa base: usar Python 3.11 slim
# ---------------------------
    FROM python:3.11.9-slim

    # Evitar escritura de .pyc y buffering
    ENV PYTHONDONTWRITEBYTECODE=1
    ENV PYTHONUNBUFFERED=1
    
    # Definir directorio de trabajo
    WORKDIR /app
    
    # Instalar dependencias del sistema necesarias para OR-Tools y demás librerías
    RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        && rm -rf /var/lib/apt/lists/*
    
    # Copiar requerimientos primero (para aprovechar cache de capas)
    COPY requirements-prod.txt .
    
    # Instalar dependencias Python
    RUN pip install --upgrade pip && pip install -r requirements-prod.txt
    
    # Copiar el resto del proyecto
    COPY . .
    
    # Exponer el puerto de la API
    EXPOSE 8000
    
    # Comando por defecto para lanzar la API
    CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
    