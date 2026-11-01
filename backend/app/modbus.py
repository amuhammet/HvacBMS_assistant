import asyncio
from datetime import datetime, timezone
from typing import Any
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient

from app.adapters.base import BaseAdapter, PointValue


class ModbusTCPAdapter(BaseAdapter):
    """Modbus TCP protokolü için adapter"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        # config fields:
        # - host: str
        # - port: int (default 502)
        # - slave_id: int (default 1)
        self.client = AsyncModbusTcpClient(
            host=config.get("host", "127.0.0.1"),
            port=config.get("port", 502),
        )
        self.slave_id = config.get("slave_id", 1)
    
    async def connect(self) -> bool:
        try:
            await self.client.connect()
            self.connected = True
            return True
        except Exception as e:
            print(f"Modbus TCP connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        await self.client.close()
        self.connected = False
    
    async def read_point(self, point_id: str) -> PointValue:
        """Modbus register'ı oku (holding/input/coil/discrete)"""
        if not self.connected:
            raise ConnectionError("Modbus adapter not connected")
        
        # TODO: point_id'yi register address'e map et
        # Örnek: "h100" → holding register 100
        # result = await client.read_holding_registers(...)
        
        raise NotImplementedError("Modbus read implementation pending")
    
    async def write_point(self, point_id: str, value: Any, priority: int = 8) -> bool:
        """Modbus register'a yazma"""
        if not self.connected:
            raise ConnectionError("Modbus adapter not connected")
        
        # TODO: await client.write_registers(...)
        
        raise NotImplementedError("Modbus write implementation pending")
    
    async def read_points(self) -> list[PointValue]:
        raise NotImplementedError("Modbus read_points implementation pending")
    
    async def write_points(self, values: dict[str, Any]) -> dict[str, bool]:
        results = {}
        for point_id, value in values.items():
            try:
                results[point_id] = await self.write_point(point_id, value)
            except Exception:
                results[point_id] = False
        return results


class ModbusRTUAdapter(BaseAdapter):
    """Modbus RTU (serial) protokolü için adapter"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        # config fields:
        # - port: str ("/dev/ttyUSB0" or "COM3")
        # - baudrate: int (default 9600)
        # - slave_id: int (default 1)
        self.client = AsyncModbusSerialClient(
            port=config.get("port", "/dev/ttyUSB0"),
            baudrate=config.get("baudrate", 9600),
            method="rtu",
        )
        self.slave_id = config.get("slave_id", 1)
    
    async def connect(self) -> bool:
        try:
            await self.client.connect()
            self.connected = True
            return True
        except Exception as e:
            print(f"Modbus RTU connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        await self.client.close()
        self.connected = False
    
    # read_point, write_point vs. ModbusTCP ile aynı mantık
    async def read_point(self, point_id: str) -> PointValue:
        raise NotImplementedError("Modbus RTU read implementation pending")
    
    async def write_point(self, point_id: str, value: Any, priority: int = 8) -> bool:
        raise NotImplementedError("Modbus RTU write implementation pending")
    
    async def read_points(self) -> list[PointValue]:
        raise NotImplementedError("Modbus RTU read_points implementation pending")
    
    async def write_points(self, values: dict[str, Any]) -> dict[str, bool]:
        results = {}
        for point_id, value in values.items():
            try:
                results[point_id] = await self.write_point(point_id, value)
            except Exception:
                results[point_id] = False
        return results
