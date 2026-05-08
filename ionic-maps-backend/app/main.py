from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Cargar variables de entorno al inicio absoluto
load_dotenv()

from app.database import connect_to_mongo, close_mongo_connection
from app.services.ml_service import MLService
from app.routers import routes, incidents, trips, weather, favorites, settings, convoy, agent
from app.config import get_settings

app_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionar ciclo de vida de la aplicación"""
    # Startup
    await connect_to_mongo()
    await MLService.load_model()
    print("🚀 API iniciada correctamente")
    
    yield
    
    # Shutdown
    await close_mongo_connection()
    print("👋 API detenida")


app = FastAPI(
    title="Ionic Maps API",
    description="""
    API para la aplicación de mapas con predicción ML de tiempos de ruta.
    
    ## Características:
    - 🗺️ **Rutas**: Cálculo de rutas con OSRM
    - 🤖 **ML**: Predicción de tiempos basada en datos históricos
    - 🌦️ **Clima**: Integración con OpenWeatherMap
    - ⚠️ **Incidencias**: Sistema de reporte de incidencias en ruta
    - 📊 **Entrenamiento**: El modelo aprende de tus viajes reales
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import WebSocket, WebSocketDisconnect
from app.services.socket_service import socket_manager

# Routers
app.include_router(trips.router)
app.include_router(weather.router)
app.include_router(routes.router)
app.include_router(incidents.router)
app.include_router(favorites.router)
app.include_router(settings.router)
app.include_router(convoy.router)
app.include_router(agent.router)

@app.websocket("/ws/caitlyn")
async def websocket_endpoint(websocket: WebSocket):
    await socket_manager.connect(websocket)
    try:
        while True:
            # Esperamos cualquier mensaje del cliente o simplemente mantenemos vivo el socket
            await websocket.receive_text()
    except WebSocketDisconnect:
        socket_manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ Error en websocket: {e}")
        socket_manager.disconnect(websocket)



@app.get("/")
async def root():
    """Endpoint de salud"""
    return {
        "status": "ok",
        "message": "🗺️ Ionic Maps API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check"""
    trips_count = 0
    try:
        from app.services.trip_service import TripService
        trips_count = await TripService.get_trips_count()
    except:
        pass
    
    return {
        "status": "healthy",
        "ml_model_trained": MLService.is_trained,
        "trips_registered": trips_count
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=app_settings.host,
        port=app_settings.port,
        reload=app_settings.debug
    )
