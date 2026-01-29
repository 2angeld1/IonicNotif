from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pickle
import os
import json

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    text: str
    user_location: Optional[List[float]] = None

class AgentResponse(BaseModel):
    intent: str
    message: str
    data: dict

# Cargar el modelo al inicio (Force Reload 2)
model_path = "app/ai/brain.pkl"
brain = None

if os.path.exists(model_path):
    with open(model_path, "rb") as f:
        brain = pickle.load(f)
else:
    print("⚠️ ADVERTENCIA: No se encontró 'brain.pkl'. Ejecuta 'python train_ai.py'")

# Cargar configuración de stopwords
config_path = "app/ai/config.json"
ai_config = {
    "navigation_stopwords": [],
    "search_stopwords": []
}

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        ai_config = json.load(f)

@router.post("/parse", response_model=AgentResponse)
async def parse_intent(request: AgentRequest):
    text = request.text.lower()
    
    if not brain:
        return {
            "intent": "chat",
            "message": "Mi cerebro no está conectado. Por favor avisa a mi creador.",
            "data": {}
        }
        
    # 1. Predecir Intención
    prediction = brain.predict([text])[0]
    # Probabilidad (opcional, para saber si está seguro)
    # probs = brain.predict_proba([text]) 
    
    response_data = {}
    message = ""
    
    # 2. Lógica según intención predicha
    if prediction == "navigate":
        # Extracción simple de entidad (mejorable luego con NER)
        # Asumimos que todo lo que no sean "stopwords" de navegación es el destino
        stopwords = ai_config.get("navigation_stopwords", [])
        words = text.split()
        destination_words = [w for w in words if w not in stopwords]
        destination = " ".join(destination_words)
        
        # Fallback si no encuentra destino claro
        if not destination or len(destination) < 2:
            return {
                "intent": "chat",
                "message": "¿A dónde te gustaría ir exactamente? 🗺️",
                "data": {}
            }
            
        message = f"Entendido. Buscando la mejor ruta hacia {destination.title()}. 🚗"
        response_data = {"destination": destination}
        
    elif prediction == "search_places":
        import re
        # Extraer número si existe (por ejemplo "5 restaurantes")
        count_match = re.search(r'(\d+)', text)
        count = int(count_match.group(1)) if count_match else 4
        
        stopwords = ai_config.get("search_stopwords", [])
        words = text.split()
        query_words = [w for w in words if w not in stopwords and not w.isdigit()]
        query = " ".join(query_words)
        
        if not query:
             # Si no hay query clara, usamos la última palabra o la frase original sin números
             query = " ".join([w for w in words if not w.isdigit()])

        message = f"Buscando {count} '{query}' cerca de ti... 🔎"
        response_data = {"query": query, "count": count}

    elif prediction == "report_incident":
        # Detección de palabras clave para el tipo de incidente
        incident_type = "hazard" # Default
        if any(w in text for w in ["choque", "accidente", "colision", "golpe"]):
            incident_type = "accident"
        elif any(w in text for w in ["policia", "policía", "reten", "paco", "tongo"]):
            incident_type = "police"
        elif any(w in text for w in ["animal", "perro", "gato"]):
            incident_type = "animal"
        elif any(w in text for w in ["trafico", "tranque", "congestion"]):
            incident_type = "hazard" # O 'traffic' si existiera
        elif any(w in text for w in ["trabajo", "obra", "reparacion"]):
            incident_type = "road_work"

        message = f"Entendido, procesando reporte de {incident_type}. ⚠️"
        response_data = {"type": incident_type}

    elif prediction == "check_weather":
        stopwords = ai_config.get("weather_stopwords", [])
        words = text.split()
        loc_words = [w for w in words if w not in stopwords and w != "?"]
        location = " ".join(loc_words)
        
        if not location:
            location = "current" # Ubicación actual

        message = f"Consultando el clima para {location if location != 'current' else 'tu ubicación'}... 🌦️"
        response_data = {"location": location}

    elif prediction == "place_details":
        stopwords = ai_config.get("place_details_stopwords", [])
        words = text.split()
        place_words = [w for w in words if w not in stopwords and w != "?"]
        place = " ".join(place_words)

        message = f"Buscando información sobre '{place}'... ⭐"
        response_data = {"place": place}
        
    else: # chat
        message = "¡Hola! Soy Caitlyn 🤖. Puedo ayudarte a traficar rutas o buscar lugares."
        
    return {
        "intent": prediction,
        "message": message,
        "data": response_data
    }
