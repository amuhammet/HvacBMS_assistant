import asyncio
from datetime import datetime, timezone
from typing import Any
import json
import aiomqtt

from app.adapters.base import BaseAdapter, PointValue


class MQTTAdapter(BaseAdapter):
    """MQTT protokolü için adapter (read-only genelde)"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        # config fields:
        # - broker: str (hostname)
        # - port: int (default 1883)
        # - topic_prefix: str (örn: "hvac/zone1/")
        # - username: str (opsiyonel)
        # - password: str (opsiyonel)
        self.client = None
        self.data: dict[str, PointValue] = {}
    
    async def connect(self) -> bool:
        try:
            self.client = aiomqtt.Client(
                self.config.get("broker", "localhost"),
                port=self.config.get("port", 1883),
                username=self.config.get("username"),
                password=self.config.get("password"),
            )
            await self.client.connect()
            await self._subscribe_topics()
            self.connected = True
            return True
        except Exception as e:
            print(f"MQTT connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.disconnect()
        self.connected = False
    
    async def _subscribe_topics(self) -> None:
        """MQTT topics'e subscribe ol"""
        topic_prefix = self.config.get("topic_prefix", "hvac/")
        # TODO: subscribe("topic_prefix/#") ve message handler
        pass
    
    async def read_point(self, point_id: str) -> PointValue:
        """Cache'den oku (last received value)"""
        if point_id not in self.data:
            raise ValueError(f"Point {point_id} not found in MQTT cache")
        return self.data[point_id]
    
    async def read_points(self) -> list[PointValue]:
        return list(self.data.values())
    
    async def write_point(self, point_id: str, value: Any, priority: int = 8) -> bool:
        """MQTT publish"""
        if not self.connected:
            raise ConnectionError("MQTT adapter not connected")
        
        topic = self.config.get("topic_prefix", "hvac/") + point_id + "/set"
        # TODO: await client.publish(topic, json.dumps({"value": value
