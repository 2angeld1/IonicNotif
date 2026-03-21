# 🗺️ Ionic Maps Backend

Backend FastAPI con MongoDB para predicción de tiempos de ruta usando Machine Learning.

## 🚀 Características

- **Cálculo de rutas** con OSRM (rutas reales sobre calles)
- **Predicción ML** de tiempos basada en tus datos históricos
- **Clima en tiempo real** con OpenWeatherMap
- **Sistema de incidencias** (accidentes, trabajos, peligros, etc.)
- **Entrenamiento automático** del modelo con tus viajes

## 📦 Instalación

### 1. Requisitos previos

- Python 3.10+
- MongoDB (local o Atlas)
- (Opcional) API Key de OpenWeatherMap

### 2. Crear entorno virtual

```bash
cd ionic-maps-backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

### 5. Ejecutar

```bash
python run.py
```

La API estará disponible en: http://localhost:8000

Documentación: http://localhost:8000/docs

## 📊 Endpoints principales

### Rutas
- `POST /routes/calculate` - Calcular ruta con predicción ML
- `POST /routes/alternatives` - Obtener rutas alternativas

### Incidencias
- `POST /incidents/` - Reportar incidencia
- `GET /incidents/` - Obtener incidencias activas
- `GET /incidents/types` - Tipos de incidencias

### Viajes (entrenamiento ML)
- `POST /trips/` - Registrar viaje completado
- `GET /trips/count` - Ver cantidad de viajes
- `POST /trips/train` - Entrenar modelo ML
- `GET /trips/model-status` - Estado del modelo

### Clima
- `GET /weather/?lat=X&lng=Y` - Obtener clima

## 🤖 Machine Learning

El modelo aprende de tus viajes registrados:

1. **Registra viajes**: Cada vez que completas un viaje, guarda el tiempo real
2. **Acumula datos**: Necesitas mínimo 10 viajes
3. **Entrena**: Llama a `/trips/train`
4. **Mejores predicciones**: El modelo ajusta tiempos según:
   - Hora del día
   - Día de la semana
   - Clima
   - Incidencias
   - Distancia
   - Tus patrones personales

## 🏗️ Estructura

```
ionic-maps-backend/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Configuración
│   ├── database.py       # MongoDB connection
│   ├── models/
│   │   └── schemas.py    # Pydantic models
│   ├── routers/
│   │   ├── routes.py     # Endpoints de rutas
│   │   ├── incidents.py  # Endpoints de incidencias
│   │   ├── trips.py      # Endpoints de viajes
│   │   └── weather.py    # Endpoints de clima
│   └── services/
│       ├── ml_service.py       # Machine Learning
│       ├── weather_service.py  # OpenWeatherMap
│       ├── routing_service.py  # OSRM
│       ├── incident_service.py # Gestión incidencias
│       └── trip_service.py     # Gestión viajes
├── requirements.txt
├── run.py
└── .env
```
