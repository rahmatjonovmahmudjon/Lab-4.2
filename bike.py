"""Bike: owns its status and the legal status transitions."""
from __future__ import annotations

from enum import Enum

from .errors import (
    BikeAlreadyDockedError,
    BikeNotAvailableError,
    RepairNotAllowedError,
)


class BikeStatus(Enum):
    AVAILABLE = "AVAILABLE"  # docked and can be taken
    IN_USE = "IN_USE"        # outside any dock (in a ride)
    REPAIR = "REPAIR"        # docked, but nobody can take it


class Bike:
    def __init__(self, bike_id: str):
        if not bike_id:
            raise ValueError("bike id must not be empty")
        self._id = bike_id
        # A new bike is outside every dock until it is parked for the first time.
        self._status = BikeStatus.IN_USE

    @property
    def id(self) -> str:
        return self._id

    @property
    def status(self) -> BikeStatus:
        return self._status

    # Transitions. Only Dock calls them, together with changing its own slot,
    # so "status" and "where the bike is" can never disagree.
    def mark_parked(self) -> None:
        if self._status is not BikeStatus.IN_USE:
            raise BikeAlreadyDockedError(f"{self._id} is already in a dock")
        self._status = BikeStatus.AVAILABLE

    def mark_taken(self) -> None:
        if self._status is not BikeStatus.AVAILABLE:
            raise BikeNotAvailableError(f"{self._id} is {self._status.value}")
        self._status = BikeStatus.IN_USE

    def mark_repair(self) -> None:
        if self._status is not BikeStatus.AVAILABLE:
            raise RepairNotAllowedError(
                f"{self._id} is {self._status.value}; only a docked free bike can be repaired"
            )
        self._status = BikeStatus.REPAIR

    def mark_repaired(self) -> None:
        if self._status is not BikeStatus.REPAIR:
            raise RepairNotAllowedError(f"{self._id} is not in repair")
        self._status = BikeStatus.AVAILABLE

    def __repr__(self) -> str:
        return f"Bike({self._id!r}, {self._status.name})"
