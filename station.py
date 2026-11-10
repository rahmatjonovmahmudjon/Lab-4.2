"""Station: owns its docks and answers questions about them."""
from __future__ import annotations

from .bike import Bike, BikeStatus
from .dock import Dock
from .errors import NoBikeError, RepairNotAllowedError, StationFullError


class Station:
    def __init__(self, name: str, capacity: int):
        if not name.strip():
            raise ValueError("station name must not be empty")
        if capacity < 1:
            raise ValueError("a station needs at least one dock")
        self._name = name
        # Created here, per instance: no mutable class attribute is shared.
        self._docks = tuple(Dock(number) for number in range(1, capacity + 1))

    @property
    def name(self) -> str:
        return self._name

    @property
    def docks(self) -> tuple[Dock, ...]:
        return tuple(self._docks)  # a copy: .append() is impossible

    @property
    def capacity(self) -> int:
        return len(self._docks)

    @property
    def free_docks(self) -> int:
        return sum(1 for dock in self._docks if dock.is_free)

    def park_bike(self, bike: Bike) -> Dock:
        for dock in self._docks:
            if dock.is_free:
                dock.park(bike)
                return dock
        raise StationFullError(self._name)

    def take_bike(self) -> Bike:
        for dock in self._docks:
            if dock.bike is not None and dock.bike.status is BikeStatus.AVAILABLE:
                return dock.take_bike()
        raise NoBikeError(f"No free bike at {self._name}")

    def send_to_repair(self, bike_id: str) -> None:
        self._find_dock(bike_id).send_bike_to_repair()

    def finish_repair(self, bike_id: str) -> None:
        self._find_dock(bike_id).finish_repair()

    def _find_dock(self, bike_id: str) -> Dock:
        for dock in self._docks:
            if dock.bike is not None and dock.bike.id == bike_id:
                return dock
        raise RepairNotAllowedError(f"Bike {bike_id} is not docked at {self._name}")

    def __len__(self) -> int:
        """Number of docked bikes (free and in repair)."""
        return self.capacity - self.free_docks

    def __str__(self) -> str:
        return f"{self._name}: {len(self)}/{self.capacity} bikes"

    def __repr__(self) -> str:
        return f"Station(name={self._name!r}, capacity={self.capacity}, bikes={len(self)})"

    def __lt__(self, other: Station) -> bool:
        if not isinstance(other, Station):
            return NotImplemented
        return self.free_docks < other.free_docks
