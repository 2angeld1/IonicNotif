from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Any
from app.services.agent_service import AgentService
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    text: str
    user_location: Optional[List[float]] = None

class AgentResponse(BaseModel):
    intent: str
    message: str
    data: dict

class InvoiceRequest(BaseModel):
    imagen: str  # base64 de la imagen

class InvoiceResponse(BaseModel):
    success: bool
    productos: list
    total_detectados: int
    raw_response: Optional[str] = None
    error: Optional[str] = None

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

@router.post("/invoice", response_model=InvoiceResponse)
async def process_invoice(request: InvoiceRequest):
    """
    Endpoint para procesar facturas con Gemini Flash Vision.
    Recibe una imagen base64 y devuelve los productos detectados.
    """
    result = await InvoiceService.process_invoice(request.imagen)
    return result
