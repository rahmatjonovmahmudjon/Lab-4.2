"""Network: runs the ride (take bike / return bike) and gives the manager view."""
from __future__ import annotations

from datetime import datetime

from .errors import NoActiveRideError, RideActiveError, StationFullError
from .receipt import ReceiptPrinter
from .ride import Ride
from .rider import Rider
from .station import Station


class Network:
    MAX_FAILED_RETURNS = 2  # n: after this many failures the error carries a redirect

    def __init__(self, printer: ReceiptPrinter):
        self._printer = printer
        self._stations: dict[str, Station] = {}
        self._rides: list[Ride] = []

    @property
    def stations(self) -> tuple[Station, ...]:
        return tuple(self._stations.values())

    @property
    def history(self) -> tuple[Ride, ...]:
        return tuple(self._rides)

    def add_station(self, station: Station) -> None:
        if station.name in self._stations:
            raise ValueError(f"station {station.name} already exists")
        self._stations[station.name] = station

    def take_bike(self, rider: Rider, station: Station, now: datetime) -> Ride:
        self._require_member(station)
        if rider.has_active_ride:
            raise RideActiveError(f"{rider.name} already has an active ride")
        bike = station.take_bike()  # NoBikeError if nothing can be taken
        ride = Ride(bike, rider, station, now)
        rider.start_ride(ride)
        self._rides.append(ride)
        return ride

    def return_bike(self, rider: Rider, station: Station, now: datetime) -> Ride:
        self._require_member(station)
        ride = rider.active_ride
        if ride is None:
            raise NoActiveRideError(f"{rider.name} has no active ride")
        ride.check_end_time(now)  # fail before touching the bike
        try:
            station.park_bike(ride.bike)
        except StationFullError as full:
            failures = ride.register_failed_return()
            if failures >= self.MAX_FAILED_RETURNS:
                raise StationFullError(station.name, self._best_redirect(station)) from full
            raise
        ride.finish(station, now)
        rider.finish_ride(ride.fee)
        self._printer.print(ride)
        return ride

    def report_text(self) -> str:
        ordered = sorted(self._stations.values(), key=lambda s: (-s.free_docks, s.name))
        return "\n".join(f"{s.name}: {s.free_docks} free docks" for s in ordered)

    def report(self) -> None:
        print(self.report_text())

    def _best_redirect(self, full_station: Station) -> Station | None:
        candidates = [
            s for s in self._stations.values()
            if s is not full_station and s.free_docks > 0
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda s: (-s.free_docks, s.name))

    def _require_member(self, station: Station) -> None:
        if self._stations.get(station.name) is not station:
            raise ValueError(f"station {station.name} is not part of this network")
