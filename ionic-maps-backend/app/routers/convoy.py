from fastapi import APIRouter, HTTPException, Request, Body
from app.models.schemas import Convoy, ConvoyCreate, ConvoyJoin, ConvoyUpdate
from app.services.convoy_service import ConvoyService

from app.database import get_database

router = APIRouter(prefix="/convoy", tags=["convoy"])

def get_service(request: Request) -> ConvoyService:
    return ConvoyService(get_database())

@router.post("/create", response_model=Convoy)
async def create_convoy(
    data: ConvoyCreate,
    request: Request
):
    service = get_service(request)
    return await service.create_convoy(data)

@router.post("/join", response_model=dict)
async def join_convoy(
    data: ConvoyJoin,
    request: Request
):
    """Retorna {'convoy': Convoy, 'user_id': str}"""
    service = get_service(request)
    result = await service.join_convoy(data)
    if not result:
        raise HTTPException(status_code=404, detail="Convoy no encontrado o inactivo")
    return result

@router.post("/{convoy_id}/update", response_model=Convoy)
async def update_location(
    convoy_id: str,
    data: ConvoyUpdate,
    request: Request
):
    service = get_service(request)
    result = await service.update_member_location(convoy_id, data.user_id, data.location)
    if not result:
        raise HTTPException(status_code=404, detail="Convoy o miembro no encontrado")
    return result

@router.get("/{convoy_id}", response_model=Convoy)
async def get_convoy_status(
    convoy_id: str,
    request: Request
):
    service = get_service(request)
    result = await service.get_convoy(convoy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Convoy no encontrado")
    return result
