from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Optional, Dict
from app.services.bms_engine import bms_engine

router = APIRouter(prefix="/api/v1/control", tags=["BMS Canlı Kontrol (Read/Write)"])

class WriteRequest(BaseModel):
    device_id: str
    adapter_type: str         # "simulator", "modbus_tcp", "modbus_rtu"
    config: Dict[str, Any]    # host, port, slave_id veya seri port ayarları
    point_id: str             # "room_temp", "h100" (holding reg 100), "c5" (coil 5)
    value: Any                # Yazılacak float, int veya boolean değer
    priority: Optional[int] = 8

@router.get("/device/{device_id}/points")
async def read_all_device_points(
    device_id: str, 
    adapter_type: str = Query(..., description="simulator, modbus_tcp veya modbus_rtu"),
    host: Optional[str] = "127.0.0.1",
    port: Optional[int] = 502,
    slave_id: Optional[int] = 1,
    serial_port: Optional[str] = "/dev/ttyUSB0",
    baudrate: Optional[int] = 9600
):
    """Cihazdaki konfigüre edilmiş tüm veri noktalarını anlık okur."""
    # Dinamik konfigürasyon oluşturma
    config = {
        "host": host,
        "port": port,
        "slave_id": slave_id,
        "port_name": serial_port, # RTU için port
        "baudrate": baudrate
    }
    
    try:
        adapter = await bms_engine.get_or_create_adapter(device_id, adapter_type, config)
        points = await adapter.read_points()
        return [p.to_dict() for p in points]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cihaz okuma hatası: {str(e)}")

@router.post("/point/write")
async def write_to_device_point(payload: WriteRequest):
    """Belirli bir veri noktasına anlık setpoint veya komut yazar."""
    try:
        # 1. İstek tipine göre adaptörü getir veya üret (Yazma yetkisini True yapıyoruz)
        config = payload.config
        config["writable"] = True
        
        adapter = await bms_engine.get_or_create_adapter(payload.device_id, payload.adapter_type, config)
        
        if not adapter.is_writable():
            raise HTTPException(status_code=400, detail="Bu adaptör salt-okunur modda yapılandırılmış.")
            
        # 2. Değeri ilgili register veya simülatör hücresine yaz
        success = await adapter.write_point(
            point_id=payload.point_id, 
            value=payload.value, 
            priority=payload.priority
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Yazma işlemi protokol/cihaz seviyesinde reddedildi.")
            
        return {
            "status": "success",
            "device_id": payload.device_id,
            "point_id": payload.point_id,
            "written_value": payload.value,
            "priority": payload.priority
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Geçersiz veri formatı/adresi: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yazma işlemi esnasında sistem hatası: {str(e)}")
