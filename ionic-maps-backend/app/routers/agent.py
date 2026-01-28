from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import pickle
import os

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    text: str
    user_location: Optional[List[float]] = None

class AgentResponse(BaseModel):
    intent: str
    message: str
    data: dict

# Cargar el modelo al inicio
model_path = "app/ai/brain.pkl"
brain = None

if os.path.exists(model_path):
    with open(model_path, "rb") as f:
        brain = pickle.load(f)
else:
    print("⚠️ ADVERTENCIA: No se encontró 'brain.pkl'. Ejecuta 'python train_ai.py'")

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
        stopwords = ["ir", "a", "hacia", "llevame", "llévame", "ruta", "dame", "como", "llegar", "el", "la", "al"]
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
        stopwords = ["buscar", "busca", "donde", "dónde", "hay", "un", "una", "cerca", "aquí", "de", "mi", "quiero", "comer"]
        words = text.split()
        query_words = [w for w in words if w not in stopwords]
        query = " ".join(query_words)
        
        if not query:
             return {
                "intent": "chat",
                "message": "¿Qué deseas buscar? 🔍",
                "data": {}
            }

        message = f"Buscando '{query}' cerca de ti... 🔎"
        response_data = {"query": query}
        
    else: # chat
        message = "¡Hola! Soy Calitin 🤖. Puedo ayudarte a traficar rutas o buscar lugares."
        
    return {
        "intent": prediction,
        "message": message,
        "data": response_data
    }
