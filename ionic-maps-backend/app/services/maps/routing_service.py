import httpx
from typing import Optional, List, Tuple
from app.config import get_settings
from app.models.schemas import LatLng

settings = get_settings()


class RoutingService:
    """Servicio para obtener rutas usando OSRM"""
    
    @classmethod
    async def get_route(
        cls,
        start: LatLng,
        end: LatLng
    ) -> Optional[dict]:
        """Obtener ruta entre dos puntos"""
        try:
            coordinates = f"{start.lng},{start.lat};{end.lng},{end.lat}"
            url = f"{settings.osrm_base_url}/route/v1/driving/{coordinates}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "true",
                        "alternatives": "true"  # Obtener rutas alternativas
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if data["code"] != "Ok" or not data["routes"]:
                    return None
                
                return data
        except Exception as e:
            print(f"Error obteniendo ruta: {e}")
            return None
    
    @staticmethod
    def points_near_route(
        route_coords: List[List[float]],
        point: LatLng,
        threshold_km: float = 0.5
    ) -> bool:
        """Verificar si un punto está cerca de la ruta"""
        from math import radians, sin, cos, sqrt, atan2
        
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # Radio de la Tierra en km
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            return R * c
        
        # Revisar cada punto de la ruta
        for coord in route_coords:
            lng, lat = coord[0], coord[1]
            distance = haversine(lat, lng, point.lat, point.lng)
            if distance <= threshold_km:
                return True
        
        return False
