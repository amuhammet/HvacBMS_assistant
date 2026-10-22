import random
from datetime import datetime, timezone

from app.adapters.base import DeviceAdapter


class SimulatorAdapter:
    name = "simulator"

    def read_points(self) -> list[dict[str, object]]:
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "point_id": "sim-supply-temp",
                "value": round(17.8 + random.uniform(-0.6, 0.6), 1),
                "unit": "°C",
                "quality": "good",
                "observed_at": now,
            },
            {
                "point_id": "sim-outdoor-temp",
                "value": round(12.4 + random.uniform(-0.8, 0.8), 1),
                "unit": "°C",
                "quality": "good",
                "observed_at": now,
            },
            {
                "point_id": "sim-humidity",
                "value": round(45 + random.uniform(-3, 3), 1),
                "unit": "%",
                "quality": "good",
                "observed_at": now,
            },
        ]
