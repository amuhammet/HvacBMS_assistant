import asyncio
from datetime import datetime, timezone
from typing import Any, Tuple
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient

from app.adapters.base import BaseAdapter, PointValue


class BaseModbusAdapter(BaseAdapter):
    """Modbus TCP ve RTU için ortak register operasyonlarını yöneten ara taban sınıf"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.client: Any = None
        self.slave_id: int = config.get("slave_id", 1)
        # Sistemde kayıtlı izlenecek point listesi (konfigürasyondan beslenir)
        self.point_definitions: dict[str, str] = config.get("points", {})

    def _parse_address(self, point_id: str) -> Tuple[str, int]:
        """
        Point ID'yi Modbus register tipine ve adresine ayrıştırır.
        Örnekler: 
          - "h100" -> ("holding", 100)
          - "i50"  -> ("input", 50)
          - "c10"  -> ("coil", 10)
          - "d20"  -> ("discrete", 20)
        """
        if not point_id or len(point_id) < 2:
            raise ValueError(f"Geçersiz Modbus Point ID formatı: {point_id}")
            
        prefix = point_id[0].lower()
        try:
            address = int(point_id[1:])
        except ValueError:
            raise ValueError(f"Modbus adresi sayısal olmalıdır: {point_id}")

        if prefix == "h":
            return "holding", address
        elif prefix == "i":
            return "input", address
        elif prefix == "c":
            return "coil", address
        elif prefix == "d":
            return "discrete", address
        else:
            raise ValueError(f"Bilinmeyen Modbus register tipi '{prefix}'. (h, i, c, d kullanılabilir)")

    async def read_point(self, point_id: str) -> PointValue:
        if not self.connected or not self.client:
            raise ConnectionError("Modbus cihazına bağlantı sağlanamadı.")

        reg_type, address = self._parse_address(point_id)
        now = datetime.now(timezone.utc)
        
        try:
            if reg_type == "holding":
                response = await self.client.read_holding_registers(address, count=1, slave=self.slave_id)
            elif reg_type == "input":
                response = await self.client.read_input_registers(address, count=1, slave=self.slave_id)
            elif reg_type == "coil":
                response = await self.client.read_coils(address, count=1, slave=self.slave_id)
            elif reg_type == "discrete":
                response = await self.client.read_discrete_inputs(address, count=1, slave=self.slave_id)

            # Pymodbus hata kontrolü
            if response.isError():
                return PointValue(point_id, None, now, quality="bad")
            
            # Değeri al (Coil/Discrete için boolean, Register için int)
            raw_value = response.bits[0] if reg_type in ["coil", "discrete"] else response.registers[0]
            
            return PointValue(point_id=point_id, value=raw_value, timestamp=now, quality="good")
            
        except Exception as e:
            print(f"Modbus okuma hatası ({point_id}): {e}")
            # Cihaz düşmüş olabilir, bağlantı durumunu kontrol etmeye zorla
            if not self.client.connected:
                self.connected = False
            return PointValue(point_id, None, now, quality="bad")

    async def write_point(self, point_id: str, value: Any, priority: int = 8) -> bool:
        """
        Modbus register'a veri yazar. 
        Not: Modbus yerel olarak BACnet gibi 'priority array' mimarisini desteklemez, 
        bu yüzden gelen priority parametresi lojikte izlenebilir ancak doğrudan cihaza sadece değer basılır.
        """
        if not self.connected or not self.client:
            raise ConnectionError("Modbus cihazına bağlantı sağlanamadı.")
        if not self.is_writable():
            print(f"Yazma reddedildi: {point_id} adaptörü salt-okunur modda.")
            return False

        reg_type, address = self._parse_address(point_id)
        
        try:
            if reg_type == "holding":
                response = await self.client.write_register(address, int(value), slave=self.slave_id)
            elif reg_type == "coil":
                response = await self.client.write_coil(address, bool(value), slave=self.slave_id)
            else:
                raise ValueError(f"Modbus üzerinde '{reg_type}' tipine yazma yapılamaz. Yalnızca Holding (h) ve Coil (c) yazılabilirdir.")

            if response.isError():
                return False
            return True
            
        except Exception as e:
            print(f"Modbus yazma hatası ({point_id} -> {value}): {e}")
            if not self.client.connected:
                self.connected = False
            return False

    async def read_points(self) -> list[PointValue]:
        """Konfigürasyondaki tanımlı veya aktif olarak sorgulanan tüm noktaları okur"""
        if not self.point_definitions:
            return []
            
        tasks = [self.read_point(pid) for pid in self.point_definitions.keys()]
        return list(await asyncio.gather(*tasks))


class ModbusTCPAdapter(BaseModbusAdapter):
    """Modbus TCP protokolü için optimize edilmiş ve tamamlanmış adapter"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.client = AsyncModbusTcpClient(
            host=config.get("host", "127.0.0.1"),
            port=config.get("port", 502),
        )
    
    async def connect(self) -> bool:
        try:
            connected = await self.client.connect()
            self.connected = connected
            return connected
        except Exception as e:
            print(f"Modbus TCP bağlantı hatası ({self.config.get('host')}): {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()
        self.connected = False


class ModbusRTUAdapter(BaseModbusAdapter):
    """Modbus RTU (Seri Port RS-485) protokolü için optimize edilmiş ve tamamlanmış adapter"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.client = AsyncModbusSerialClient(
            port=config.get("port", "/dev/ttyUSB0"),
            baudrate=config.get("baudrate", 9600),
            stopbits=config.get("stopbits", 1),
            bytesize=config.get("bytesize", 8),
            parity=config.get("parity", "N"),
            method="rtu",
        )
    
    async def connect(self) -> bool:
        try:
            connected = await self.client.connect()
            self.connected = connected
            return connected
        except Exception as e:
            print(f"Modbus RTU seri port bağlantı hatası ({self.config.get('port')}): {e}")
            self.connected = False
            return False
    
    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()
        self.connected = False
