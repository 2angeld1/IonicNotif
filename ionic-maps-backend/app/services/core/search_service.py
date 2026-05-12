import httpx
from typing import List, Dict, Any, Optional

class SearchService:
    """Servicio para buscar lugares (POIs) usando OpenStreetMap (Nominatim)"""
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    USER_AGENT = "IonicNotif-App/1.0"

    @classmethod
    async def find_nearby_places(
        cls, 
        query: str, 
        lat: float, 
        lng: float, 
        radius_km: float = 5.0,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Busca lugares cercanos a una ubicación.
        """
        try:
            # Nominatim usa un formato un poco diferente para búsqueda cercana
            # Podríamos usar 'q' para la búsqueda general
            params = {
                "q": query,
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
                "viewbox": f"{lng - 0.1},{lat + 0.1},{lng + 0.1},{lat - 0.1}", # Una caja de búsqueda aproximada
                "bounded": 1
            }
            
            headers = {"User-Agent": cls.USER_AGENT}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(cls.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data:
                    results.append({
                        "name": item.get("display_name"),
                        "lat": float(item.get("lat")),
                        "lng": float(item.get("lon")),
                        "type": item.get("type"),
                        "category": item.get("category")
                    })
                return results
        except Exception as e:
            print(f"Error en SearchService: {e}")
            return []
