from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from app.services.bms_engine import bms_engine

router = APIRouter(prefix="/api/v1/control", tags=["BMS Canlı Kontrol"])

class WritePayload(BaseModel):
    device_id: str
    adapter_type: str
    config: dict
    point_id: str
    value: Any
    priority: Optional[int] = 8

@router.get("/device/{device_id}/points")
async def get_device_points(device_id: str, adapter_type: str, writable: bool = True):
    """Cihazdaki tüm anlık point verilerini listeler."""
    config = {"writable": writable}
    adapter = await bms_engine.get_or_create_adapter(device_id, adapter_type, config)
    
    points = await adapter.read_points()
    return [p.to_dict() for p in points]

@router.post("/point/write")
async def write_point_value(payload: WritePayload):
    """Belirli bir noktaya yeni değer yazar."""
    adapter = await bms_engine.get_or_create_adapter(
        payload.device_id, payload.adapter_type, payload.config
    )
    
    if not adapter.is_writable():
        raise HTTPException(status_code=400, detail="Bu adaptör yazma modunda konfigüre edilmemiş.")
        
    success = await adapter.write_point(
        point_id=payload.point_id, 
        value=payload.value, 
        priority=payload.priority
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Yazma işlemi adaptör katmanında başarısız oldu.")
        
    return {"status": "success", "point_id": payload.point_id, "new_value": payload.value}
