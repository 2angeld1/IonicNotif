from mcp.server.fastmcp import FastMCP
from app.services.weather_service import WeatherService
from app.services.routing_service import RoutingService
from app.services.search_service import SearchService
from app.models.schemas import LatLng

# Crear el servidor MCP de IonicNotif
mcp = FastMCP("IonicNotif Core APIs")

# Flag para saber si MongoDB ya está conectado
_mongo_ready = False

async def _ensure_mongo():
    """Conexión lazy a MongoDB — solo al primer uso."""
    global _mongo_ready
    if not _mongo_ready:
        from app.database import connect_to_mongo
        await connect_to_mongo()
        _mongo_ready = True

# ─── Herramientas que NO necesitan MongoDB ───

@mcp.tool()
async def get_weather_info(lat: float, lng: float) -> str:
    """Obtiene el clima actual para una ubicación."""
    weather = await WeatherService.get_weather(lat, lng)
    if weather:
        return f"Clima: {weather.condition.name}, Temperatura: {weather.temperature}°C, Detalle: {weather.description}"
    return "Error al obtener datos del clima."

@mcp.tool()
async def search_nearby_places(query: str, lat: float, lng: float, radius_km: float = 5.0) -> str:
    """
    Busca lugares (farmacias, gasolineras, comida, etc) cerca de una ubicación.
    Útil para añadir paradas a una ruta.
    """
    places = await SearchService.find_nearby_places(query, lat, lng, radius_km)
    if not places:
        return f"No se encontraron '{query}' cerca de esa ubicación."
    
    result = f"Lugares encontrados para '{query}':\n"
    for i, p in enumerate(places, 1):
        result += f"{i}. {p['name']} (lat={p['lat']}, lng={p['lng']})\n"
    return result

@mcp.tool()
async def calculate_route_metrics(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> str:
    """Calcula distancia y tiempo de viaje entre dos puntos usando OSRM."""
    start = LatLng(lat=start_lat, lng=start_lng)
    end = LatLng(lat=end_lat, lng=end_lng)
    route_data = await RoutingService.get_route(start, end)
    if route_data and route_data.get("routes"):
        main_route = route_data["routes"][0]
        duration = int(main_route.get("duration", 0) / 60)
        distance = round(main_route.get("distance", 0) / 1000, 2)
        return f"Ruta calculada: {distance} km, tiempo estimado: {duration} minutos."
    return "No se encontró ruta viable."

# ─── Herramientas que SÍ necesitan MongoDB (lazy connect) ───

@mcp.tool()
async def get_my_favorite_places() -> str:
    """Lista los lugares favoritos del usuario (Casa, Trabajo, etc) con coordenadas."""
    await _ensure_mongo()
    from app.services.favorite_service import FavoriteService
    favorites = await FavoriteService.get_favorites()
    if not favorites:
        return "No tienes lugares favoritos guardados."
    result = "Tus lugares favoritos:\n"
    for fav in favorites:
        loc = fav.get("location", {})
        result += f"- {fav.get('name')}: lat={loc.get('lat')}, lng={loc.get('lng')}\n"
    return result

@mcp.tool()
async def report_road_incident(lat: float, lng: float, description: str, incident_type: str = "hazard") -> str:
    """Reporta una incidencia vial (accident, police, hazard, road_work, animal)."""
    await _ensure_mongo()
    from app.services.incident_service import IncidentService
    from app.models.schemas import IncidentCreate, IncidentType, IncidentSeverity
    try:
        inc_type = IncidentType(incident_type.lower())
    except ValueError:
        inc_type = IncidentType.HAZARD
    incident = IncidentCreate(
        location=LatLng(lat=lat, lng=lng),
        type=inc_type,
        severity=IncidentSeverity.MEDIUM,
        description=description
    )
    result = await IncidentService.create_incident(incident)
    return f"Incidencia '{incident_type}' reportada en {lat}, {lng}."

@mcp.tool()
async def set_active_navigation(stops_json: str) -> str:
    """
    Establece la ruta de navegación activa en el mapa. 
    ÚSALO SIEMPRE que confirmes una ruta al usuario (ej: 'Te llevo a casa pasando por la farmacia').
    'stops_json' debe ser un JSON string con la lista de coordenadas, 
    ej: '[{"lat": 8.98, "lng": -79.5}, {"lat": 9.01, "lng": -79.52}]'.
    Incluye todos los puntos: origen (si es distinto a ubicación actual), paradas y destino final.
    """
    # Esta herramienta es una señal para el backend. No necesita lógica aquí.
    return f"Señal de navegación emitida con {stops_json}. El GPS procesará la ruta."

@mcp.tool()
async def check_nearby_incidents(lat: float, lng: float, radius_km: float = 10.0) -> str:
    """Busca peligros reportados cerca de una ubicación."""
    await _ensure_mongo()
    from app.services.incident_service import IncidentService
    incidents = await IncidentService.get_active_incidents(
        near_location=LatLng(lat=lat, lng=lng),
        radius_km=radius_km
    )
    if not incidents:
        return f"No hay incidentes en un radio de {radius_km} km."
    result = f"Se detectaron {len(incidents)} eventos:\n"
    for inc in incidents:
        result += f"- {inc.type.value}: {inc.description}\n"
    return result

if __name__ == "__main__":
    mcp.run()
