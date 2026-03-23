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

from fastapi.responses import JSONResponse

@router.post("/invoice")
async def process_invoice(request: InvoiceRequest):
    """
    Endpoint para procesar facturas con Gemini Flash Vision.
    Recibe una imagen base64 y devuelve los productos detectados.
    """
    result = await InvoiceService.process_invoice(request.imagen)
    # 🏁 BLINDAJE DE TILDES: Forzamos UTF-8 puro sin escapes ASCII
    return JSONResponse(content=result)

class DashboardAlertsRequest(BaseModel):
    alerts: list

class StrategicAdviceRequest(BaseModel):
    product_name: Optional[str] = None
    market_context: dict
    business_data: dict
    config: Optional[dict] = None

@router.post("/business/dashboard-alerts")
async def get_dashboard_summary(request: DashboardAlertsRequest):
    """
    Caitlyn genera un resumen a partir de las alertas de rentabilidad pasadas por la app.
    """
    result = await BusinessService.get_dashboard_summary(request.alerts)
    return result

@router.post("/business/advice")
async def get_strategic_advice(payload: dict):
    return await BusinessService.get_strategic_advice(payload)

@router.post("/recipe/suggest")
async def suggest_recipe(payload: dict):
    dish_name = payload.get("dish_name")
    inventory_list = payload.get("inventory", [])
    serving_size = payload.get("serving_size")
    market_context = payload.get("market_context")
    target_margin = payload.get("target_margin", 65)

    if not dish_name:
        return {"success": False, "error": "Falta el nombre del plato"}
    return await BusinessService.suggest_recipe(
        dish_name, 
        inventory_list, 
        serving_size, 
        market_context, 
        target_margin
    )

@router.post("/menu-ideas/suggest")
async def suggest_menu_ideas(payload: dict):
    inventory_list = payload.get("inventory_list", [])
    target_margin = payload.get("target_margin", 65)
        
    return await BusinessService.suggest_menu_from_inventory(
        inventory_list, 
        target_margin
    )

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
