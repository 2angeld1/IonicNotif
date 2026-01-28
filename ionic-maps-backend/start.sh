#!/bin/bash

# 1. Entrenar la IA (Crea el brain.pkl fresco)
echo "🧠 Entrenando IA de Navegación..."
python train_ai.py

# 2. Iniciar el servidor
echo "🚀 Iniciando Ionic Notif Backend..."
# Usamos el puerto asignado por Railway ($PORT) o 8000 por defecto
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
