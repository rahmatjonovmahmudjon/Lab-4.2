"""Dock: holds at most one bike and protects that rule."""
from __future__ import annotations

from .bike import Bike
from .errors import DockOccupiedError, NoBikeError, RepairNotAllowedError


class Dock:
    def __init__(self, number: int):
        self._number = number
        self._bike: Bike | None = None

    @property
    def number(self) -> int:
        return self._number

    @property
    def bike(self) -> Bike | None:
        return self._bike

    @property
    def is_free(self) -> bool:
        return self._bike is None

    def park(self, bike: Bike) -> None:
        if self._bike is not None:
            raise DockOccupiedError(f"Dock {self._number} is occupied")
        bike.mark_parked()  # raises if the bike is already docked somewhere
        self._bike = bike

    def take_bike(self) -> Bike:
        if self._bike is None:
            raise NoBikeError(f"Dock {self._number} is empty")
        self._bike.mark_taken()  # raises if the bike is in repair
        bike, self._bike = self._bike, None
        return bike

    def send_bike_to_repair(self) -> None:
        if self._bike is None:
            raise RepairNotAllowedError(f"Dock {self._number} is empty")
        self._bike.mark_repair()

    def finish_repair(self) -> None:
        if self._bike is None:
            raise RepairNotAllowedError(f"Dock {self._number} is empty")
        self._bike.mark_repaired()
