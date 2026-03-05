import os
import json
import pickle
import re
from typing import Optional, List, Dict, Any
from app.services.hive_service import HiveService

class AgentService:
    # Rutas de modelos y configuración
    MODEL_PATH = "app/ai/brain.pkl"
    CONFIG_PATH = "app/ai/config.json"
    
    _brain = None
    _config = {
        "navigation_stopwords": [],
        "search_stopwords": [],
        "weather_stopwords": [],
        "place_details_stopwords": []
    }

    @classmethod
    def initialize(cls):
        """Carga el modelo y la configuración en memoria."""
        if os.path.exists(cls.MODEL_PATH):
            try:
                with open(cls.MODEL_PATH, "rb") as f:
                    cls._brain = pickle.load(f)
                print("🧠 AgentService: Cerebro cargado correctamente.")
            except Exception as e:
                print(f"⚠️ AgentService: Error cargando cerebro: {e}")

        if os.path.exists(cls.CONFIG_PATH):
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    cls._config = json.load(f)
            except Exception as e:
                print(f"⚠️ AgentService: Error cargando config: {e}")

    @classmethod
    async def process_request(cls, text: str, user_location: Optional[List[float]] = None) -> Dict[str, Any]:
        """Procesa una solicitud de usuario y devuelve una intención y mensaje."""
        text_lower = text.lower()
        
        # 1. Prioridad: Delegación a Hive (por complejidad o palabra clave)
        use_hive = os.getenv("USE_HIVE", "True").lower() == "true"
        if use_hive and ("hive" in text_lower or len(text_lower.split()) > 10):
            return await cls._process_with_hive(text)

        # 2. Procesamiento local con brain.pkl
        if not cls._brain:
            cls.initialize()

        prediction = "chat"
        if cls._brain:
            try:
                prediction = cls._brain.predict([text_lower])[0]
            except:
                prediction = "chat"

        # 3. Mapeo de intención a datos
        return await cls._map_prediction_to_response(prediction, text)

    @classmethod
    async def _process_with_hive(cls, text: str) -> Dict[str, Any]:
        """Delega la inteligencia a Hive y extrae metadatos de la respuesta."""
        print(f"📡 Delegando a Hive: '{text[:50]}...'")
        result = await HiveService.get_response(text)
        
        # Manejar si es un dict (nuevo formato) o balancear a str (compatibilidad)
        if isinstance(result, dict):
            hive_response = str(result.get("message", ""))
            structured_locations = result.get("locations", [])
        else:
            hive_response = str(result)
            structured_locations = []

        intent = "chat"
        data: Dict[str, Any] = {}
        
        # 1. Obtención de Ubicaciones (Prioridad Estructurada > Regex)
        coord_matches = re.findall(r'\(?\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\s*\)?', hive_response)
        
        if structured_locations:
            data["locations"] = structured_locations
            intent = "navigate" # Si hay paradas explícitas, la intención es navegar
        elif coord_matches:
            data["locations"] = [
                {"lat": float(m[0]), "lng": float(m[1])}
                for m in coord_matches
            ]

        # Si solo hay una, mantenemos la compatibilidad
        if data.get("locations") and len(data["locations"]) == 1:
            data["location"] = data["locations"][0]

        # 2. Detección de navegación/ruta (Refuerzo por keywords)
        text_for_intent = hive_response.lower()
        if intent != "navigate" and any(w in text_for_intent for w in ["km", "minutos", "distancia", "ruta a", "llevo", "dirígete", "navega"]):
            intent = "navigate"
            # Extraer Destino
            to_match = re.search(r'(?:hacia|a|destino|en|para|hasta|llegar a)\s+\*?\*?([A-Z][a-z0-9\s]+|casa|trabajo|farmacia|gasolinera|supermercado)\*?\*?', hive_response, re.IGNORECASE)
            
            dest_str = to_match.group(1).strip() if to_match else ""
            
            # Extraer Origen
            from_match = re.search(r'(?:desde|de|partiendo de)\s+\*?\*?([A-Z][a-z0-9\s]+|casa|trabajo)\*?\*?', hive_response, re.IGNORECASE)
            origin_str = from_match.group(1).strip() if from_match else ""

            # 🛠️ VALIDACIÓN DE COHERENCIA: Evitar origen==destino si no hay coords
            if dest_str.lower() == origin_str.lower() and not data.get("locations"):
                origin_str = "" # Forzar origen a ubicación actual si son iguales por error de regex

            if dest_str:
                data["destination"] = dest_str
                data["isFavorite"] = any(fav in dest_str.lower() for fav in ["casa", "trabajo"])
            
            if origin_str:
                data["origin"] = origin_str

        # 3. Detección de búsqueda (si Hive encontró varios lugares)
        elif any(w in text_for_intent for w in ["encontrado", "lista de", "ubicaciones", "lugares", "resultados"]):
            if coord_matches:
                intent = "search_places"
                data["query"] = text

        return {
            "intent": intent,
            "message": hive_response,
            "data": data
        }

    @classmethod
    async def _map_prediction_to_response(cls, prediction: str, text: str) -> Dict[str, Any]:
        """Convierte una predicción de IA local en una respuesta estructurada."""
        text_lower = text.lower()
        message = ""
        data = {}

        if prediction == "navigate":
            destination = cls._extract_entity(text_lower, "navigation_stopwords")
            if not destination or len(destination) < 2:
                return {
                    "intent": "chat",
                    "message": "¿A dónde te gustaría ir exactamente? 🗺️",
                    "data": {}
                }
            message = f"Entendido. Buscando la mejor ruta hacia {destination.title()}. 🚗"
            data = {"destination": destination}

        elif prediction == "search_places":
            count_match = re.search(r'(\d+)', text_lower)
            count = int(count_match.group(1)) if count_match else 4
            query = cls._extract_entity(text_lower, "search_stopwords", filter_digits=True)
            
            if not query:
                # Fallback: quitar números y usar lo que quede
                query = " ".join([w for w in text_lower.split() if not w.isdigit()])

            message = f"Buscando {count} '{query}' cerca de ti... 🔎"
            data = {"query": query, "count": count}

        elif prediction == "report_incident":
            incident_type = cls._detect_incident_type(text_lower)
            message = f"Entendido, procesando reporte de {incident_type}. ⚠️"
            data = {"type": incident_type}

        elif prediction == "check_weather":
            location = cls._extract_entity(text_lower, "weather_stopwords")
            if not location or "?" in location:
                location = "current"
            
            message = f"Consultando el clima para {location if location != 'current' else 'tu ubicación'}... 🌦️"
            data = {"location": location}

        elif prediction == "place_details":
            place = cls._extract_entity(text_lower, "place_details_stopwords")
            message = f"Buscando información sobre '{place}'... ⭐"
            data = {"place": place}

        else: # chat
            use_hive = os.getenv("USE_HIVE", "True").lower() == "true"
            if use_hive:
                message = await HiveService.get_response(text)
            else:
                message = "Caitlyn (Local): ¡Hola! Por ahora solo puedo ayudarte con rutas directas, clima o reportes. Para razonamiento avanzado, necesito conectar mis motores de Hive."
            prediction = "chat"

        return {
            "intent": prediction,
            "message": message,
            "data": data
        }

    @classmethod
    def _extract_entity(cls, text: str, stopword_key: str, filter_digits: bool = False) -> str:
        """Limpia el texto de stopwords y retorna el resto como entidad."""
        stopwords = cls._config.get(stopword_key, [])
        words = text.split()
        entity_words = [w for w in words if w not in stopwords]
        
        if filter_digits:
            entity_words = [w for w in entity_words if not w.isdigit()]
            
        return " ".join(entity_words).strip()

    @classmethod
    def _detect_incident_type(cls, text: str) -> str:
        """Detecta el tipo de incidente basado en palabras clave."""
        if any(w in text for w in ["choque", "accidente", "colision", "golpe"]):
            return "accident"
        if any(w in text for w in ["policia", "policía", "reten", "paco", "tongo"]):
            return "police"
        if any(w in text for w in ["animal", "perro", "gato"]):
            return "animal"
        if any(w in text for w in ["trabajo", "obra", "reparacion"]):
            return "road_work"
        return "hazard"
