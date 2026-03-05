from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Any
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    text: str
    user_location: Optional[List[float]] = None

class AgentResponse(BaseModel):
    intent: str
    message: str
    data: dict

@router.on_event("startup")
async def startup_event():
    # Inicializar el servicio de agentes al arrancar la app
    AgentService.initialize()

@router.post("/parse", response_model=AgentResponse)
async def parse_intent(request: AgentRequest):
    """
    Endpoint principal para procesar peticiones de voz/texto.
    Delega la lógica al AgentService.
    """
    result = await AgentService.process_request(
        request.text, 
        request.user_location
    )
    return result
