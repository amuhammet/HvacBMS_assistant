import asyncio
from datetime import datetime, timezone
from typing import Any
from random import random

from app.adapters.base import BaseAdapter, PointValue


class SimulatorAdapter(BaseAdapter):
    """Simülasyon ortamı için adapter"""
    
    def __init__(self, config: dict[str, Any] = None):
        super().__init__(config or {"writable": True})
        self.data: dict[str, PointValue] = {}
        self._load_initial_data()
    
    async def connect(self) -> bool:
        self.connected = True
        return True
    
    async def disconnect(self) -> None:
        self.connected = False
    
    def _load_initial_data(self) -> None:
        """Simüle edilmiş data yükle"""
        self.data = {
            "1": PointValue("1", 22.5, datetime.now(timezone.utc), "good", "°C"),
            "2": PointValue("2", 45.0, datetime.now(timezone.utc), "good", "%"),
            "3": PointValue("3", 1200, datetime.now(timezone.utc), "good", "W"),
        }
    
    async def read_point(self, point_id: str) -> PointValue:
        if point_id not in self.data:
            raise ValueError(f"Point {point_id} not found")
        
        # Gerçekçi simülasyon: hafif değişiklik ekle
        pv = self.data[point_id]
        noise = (random() - 0.5) * 0.5
        return PointValue(
            pv.point_id,
            pv.value + noise,
            datetime.now(timezone.utc),
            "good",
            pv.unit,
        )
    
    async def read_points(self) -> list[PointValue]:
        return [await self.read_point(pid) for pid in self.data.keys()]
    
    async def write_point(self, point_id: str, value: Any, priority: int = 8) -> bool:
        if point_id not in self.data:
            raise ValueError(f"Point {point_id} not found")
        
        self.data[point_id].value = value
        self.data[point_id].timestamp = datetime.now(timezone.utc)
        return True
    
    async def write_points(self, values: dict[str, Any]) -> dict[str, bool]:
        results = {}
        for point_id, value in values.items():
            try:
                results[point_id] = await self.write_point(point_id, value)
            except ValueError:
                results[point_id] = False
        return results
