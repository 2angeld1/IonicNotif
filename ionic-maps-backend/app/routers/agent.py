from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Any
from app.services.agent_service import AgentService
from app.services.invoice_service import InvoiceService
from app.services.business_service import BusinessService
from fastapi import Header

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
    fiscal: Optional[dict] = None
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

class DashboardAlertsRequest(BaseModel):
    alerts: list

@router.post("/business/dashboard-alerts")
async def get_dashboard_summary(request: DashboardAlertsRequest):
    """
    Caitlyn genera un resumen a partir de las alertas de rentabilidad pasadas por la app.
    """
    result = await BusinessService.get_dashboard_summary(request.alerts)
    return result

@router.get("/business/advice")
async def get_business_advice(product_name: str, authorization: str = Header(...)):
    """
    Caitlyn analiza un producto de Kitchy y da su consejo pro.
    Recibe el token de Kitchy para poder consultar los datos reales.
    """
    # Extraer el token puro (Bearer <token>)
    token = authorization.split(" ")[1] if " " in authorization else authorization
    
    result = await BusinessService.get_advice(product_name, token)
    return result
