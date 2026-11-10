"""All domain errors of the bike sharing app."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .station import Station


class BikeSharingError(Exception):
    """Base class, so callers can catch every app error at once."""


class DockOccupiedError(BikeSharingError):
    """A bike was parked into a dock that already holds a bike."""


class BikeAlreadyDockedError(BikeSharingError):
    """A bike that is already in a dock was parked again."""


class BikeNotAvailableError(BikeSharingError):
    """A bike that is not AVAILABLE (in repair / in use) was taken."""


class RepairNotAllowedError(BikeSharingError):
    """Only a docked, free (AVAILABLE) bike can be sent to repair."""


class NoBikeError(BikeSharingError):
    """The station (or dock) has no free bike to take."""


class RideActiveError(BikeSharingError):
    """The rider already has an active ride."""


class NoActiveRideError(BikeSharingError):
    """The rider tried to return a bike without an active ride."""


class RideFinishedError(BikeSharingError):
    """The ride is already finished."""


class StationFullError(BikeSharingError):
    """No free dock at the station. May carry a redirect station."""

    def __init__(self, station_name: str, redirect: Station | None = None):
        self._station_name = station_name
        self._redirect = redirect
        message = f"Station {station_name} is full"
        if redirect is not None:
            message += f"; return the bike to {redirect.name} instead"
        super().__init__(message)

    @property
    def station_name(self) -> str:
        return self._station_name

    @property
    def redirect(self) -> Station | None:
        return self._redirect
