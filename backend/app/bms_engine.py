from typing import Dict
from app.adapters.base import BaseAdapter
from app.adapters.simulator import SimulatorAdapter

class BMSEngine:
    """Projedeki aktif cihaz bağlantılarını ve adaptörleri yöneten servis."""
    
    def __init__(self):
        # Key: device_id veya project_id, Value: BaseAdapter instance
        self.active_adapters: Dict[str, BaseAdapter] = {}

    async def get_or_create_adapter(self, device_id: str, adapter_type: str, config: dict) -> BaseAdapter:
        if device_id not in self.active_adapters:
            if adapter_type == "simulator":
                adapter = SimulatorAdapter(config)
            # future: elif adapter_type == "bacnet": adapter = BACnetAdapter(config)
            else:
                raise ValueError(f"Bilinmeyen adaptör tipi: {adapter_type}")
                
            await adapter.connect()
            self.active_adapters[device_id] = adapter
            
        return self.active_adapters[device_id]

    async def shutdown(self):
        """Ugulama kapanırken tüm bağlantıları temizler."""
        for adapter in self.active_adapters.values():
            await adapter.disconnect()
        self.active_adapters.clear()

bms_engine = BMSEngine()
