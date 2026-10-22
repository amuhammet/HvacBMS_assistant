from typing import Protocol


class DeviceAdapter(Protocol):
    name: str

    def read_points(self) -> list[dict[str, object]]:
        """Return the latest read-only values exposed by this adapter."""
