from abc import ABC, abstractmethod
from typing import Any, Optional
from datetime import datetime

class PointValue:
    """Read/Write için standardize edilmiş point değer"""
    def __init__(
        self,
        point_id: str,
        value: Any,
        timestamp: datetime,
        quality: str = "good",
        unit: Optional[str] = None,
    ):
        self.point_id = point_id
        self.value = value
        self.timestamp = timestamp
        self.quality = quality  # "good", "uncertain", "bad"
        self.unit = unit

    def to_dict(self) -> dict[str, Any]:
        return {
            "point_id": self.point_id,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "quality": self.quality,
            "unit": self.unit,
        }


class BaseAdapter(ABC):
    """Tüm protokol adapterleri için base class"""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Cihaza bağlan"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Cihazdan çık"""
        pass
    
    @abstractmethod
    async def read_point(self, point_id: str) -> PointValue:
        """Tek point oku"""
        pass
    
    @abstractmethod
    async def read_points(self) -> list[PointValue]:
        """Tüm points'i oku"""
        pass
    
    @abstractmethod
    async def write_point(
        self, point_id: str, value: Any, priority: int = 8
    ) -> bool:
        """Point'e yaz (BACnet priority destek)"""
        pass
    
    @abstractmethod
    async def write_points(
        self, values: dict[str, Any]
    ) -> dict[str, bool]:
        """Birden çok point'e yaz"""
        pass
    
    def is_writable(self) -> bool:
        """Adapter yazılabilir mi?"""
        return self.config.get("writable", False)
