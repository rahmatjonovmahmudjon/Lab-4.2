"""Rider: has at most one active ride and remembers what was paid."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import NoActiveRideError, RideActiveError

if TYPE_CHECKING:
    from .ride import Ride


class Rider:
    def __init__(self, name: str):
        self._name = name
        self._active_ride: Ride | None = None
        self._total_paid = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def active_ride(self) -> Ride | None:
        return self._active_ride

    @property
    def has_active_ride(self) -> bool:
        return self._active_ride is not None

    @property
    def total_paid(self) -> int:
        return self._total_paid

    def start_ride(self, ride: Ride) -> None:
        if self._active_ride is not None:
            raise RideActiveError(f"{self._name} already has an active ride")
        self._active_ride = ride

    def finish_ride(self, fee: int) -> Ride:
        if self._active_ride is None:
            raise NoActiveRideError(f"{self._name} has no active ride")
        ride, self._active_ride = self._active_ride, None
        self._total_paid += fee
        return ride

    def __repr__(self) -> str:
        return f"Rider({self._name!r})"
