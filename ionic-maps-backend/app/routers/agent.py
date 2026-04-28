from fastapi import APIRouter, Header, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
from app.services.agent_service import AgentService
from app.services.invoice_service import InvoiceService
from app.services.business_service import BusinessService
from app.services.caitlyn_vision_service import CaitlynVisionService
from app.services.shopping_service import ShoppingService
from app.services.ventas_notebook_service import VentasNotebookService
from app.services.market_service import MarketService
from fastapi.responses import JSONResponse

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
    negocio_tipo: Optional[str] = "GASTRONOMIA"

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
    Recibe una imagen base64 y el tipo de negocio.
    """
    result = await InvoiceService.process_invoice(request.imagen, request.negocio_tipo)
    # 🏁 BLINDAJE DE TILDES: Forzamos UTF-8 puro sin escapes ASCII
    return JSONResponse(content=result)

# --- Endpoints de Vision y Facturación ---

class AliasLearnRequest(BaseModel):
    invoice_text: str
    product_id: str
    negocio_id: Optional[str] = "global"

@router.post("/vision/learn-alias")
async def learn_alias(request: AliasLearnRequest):
    """
    Caitlyn aprende que un texto específico de factura corresponde a un ID de inventario.
    Segmentado por negocio.
    """
    await CaitlynVisionService.learn_alias(request.invoice_text, request.product_id, request.negocio_id)
    return {"success": True, "message": "Aprendizaje visual guardado"}

@router.post("/vision/match-products")
async def match_invoice_products(payload: dict):
    """
    Toma una lista de productos detectados por Gemini y busca sus matches en el inventario real.
    """
    invoice_items = payload.get("extracted_items", [])
    inventory_items = payload.get("inventory_items", [])
    negocio_id = payload.get("negocio_id", "global")
    
    results = []
    for item in invoice_items:
        product_id = await CaitlynVisionService.match_product_alias(item["nombre"], inventory_items, negocio_id)
        results.append({
            "original": item,
            "matched_id": product_id
        })
        
    return {"success": True, "matches": results}

class DashboardAlertsRequest(BaseModel):
    alerts: list
    negocio_id: Optional[str] = None
    user_name: Optional[str] = "Socio/a"

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
    result = await BusinessService.get_dashboard_summary(request.alerts, request.negocio_id, request.user_name)
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
        target_margin,
        payload.get("negocio_id", "global")
    )

@router.post("/menu-ideas/suggest")
async def suggest_menu_ideas(payload: dict):
    inventory_list = payload.get("inventory_list", [])
    target_margin = payload.get("target_margin", 65)
    negocio_id = payload.get("negocio_id", "global")
        
    return await BusinessService.suggest_menu_from_inventory(
        inventory_list, 
        target_margin,
        negocio_id,
        payload.get("user_name", "Socio/a")
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

# --- Caitlyn Shopping / Presupuestario ---

class ShoppingRequest(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None # base64

@router.post("/shopping/parse")
async def parse_shopping_list(request: ShoppingRequest):
    """
    Toma una lista de compras (texto o foto) y la convierte en items con precios.
    """
    result = await ShoppingService.parse_shopping_list(request.text, request.image)
    return result

class PriceReportRequest(BaseModel):
    item_name: str
    price: float
    negocio_id: str

@router.post("/shopping/learn-price")
async def learn_price(request: PriceReportRequest):
    """
    Guarda un precio real para que Caitlyn aprenda del mercado local.
    """
    await ShoppingService.save_historical_price(request.item_name, request.price, request.negocio_id)
    return {"success": True, "message": "Caitlyn aprendió el precio de " + request.item_name}

# --- Procesamiento de Cuadernos de Ventas ---

class NotebookRequest(BaseModel):
    imagen: str # base64

@router.post("/notebook")
async def process_notebook(request: NotebookRequest):
    """
    Toma una foto de una hoja de ventas de cuaderno y extrae las ventas.
    """
    result = await VentasNotebookService.process_notebook(request.imagen)
    return JSONResponse(content=result)

class MarketParseRequest(BaseModel):
    tipo: str
    imagen: Optional[str] = None

@router.post("/market/parse")
async def parse_market(request: MarketParseRequest):
    """
    Caitlyn analiza una captura de pantalla de un sitio de mercado (Playwright)
    y devuelve los precios estructurados.
    """
    result = await MarketService.parse_market_image(request.tipo, request.imagen)
    return JSONResponse(content=result)
