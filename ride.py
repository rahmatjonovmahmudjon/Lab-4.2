"""Ride: an event with data. It owns the fee rule and its failed-return counter."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from .errors import RideFinishedError

if TYPE_CHECKING:
    from .bike import Bike
    from .rider import Rider
    from .station import Station


class Ride:
    # The only place where the money rule numbers are written (DRY).
    FREE_MINUTES = 15
    BLOCK_MINUTES = 5
    PRICE_PER_BLOCK = 500   # sum
    MAX_FEE = 20_000        # sum

    def __init__(self, bike: Bike, rider: Rider, start_station: Station, start_time: datetime):
        self._bike = bike
        self._rider = rider
        self._start_station = start_station
        self._start_time = start_time
        self._end_station: Station | None = None
        self._end_time: datetime | None = None
        self._failed_returns = 0

    @property
    def bike(self) -> Bike:
        return self._bike

    @property
    def rider(self) -> Rider:
        return self._rider

    @property
    def start_station(self) -> Station:
        return self._start_station

    @property
    def end_station(self) -> Station | None:
        return self._end_station

    @property
    def start_time(self) -> datetime:
        return self._start_time

    @property
    def end_time(self) -> datetime | None:
        return self._end_time

    @property
    def is_active(self) -> bool:
        return self._end_time is None

    @property
    def failed_returns(self) -> int:
        return self._failed_returns

    @property
    def duration(self) -> timedelta:
        if self._end_time is None:
            raise ValueError("ride is not finished yet")
        return self._end_time - self._start_time

    @property
    def fee(self) -> int:
        return self.fee_for(self.duration)

    @staticmethod
    def fee_for(duration: timedelta) -> int:
        """Money rule: 15 min free, then 500 per started 5 min, capped."""
        if duration < timedelta(0):
            raise ValueError("duration must not be negative")
        over = duration - timedelta(minutes=Ride.FREE_MINUTES)
        if over <= timedelta(0):
            return 0
        block = timedelta(minutes=Ride.BLOCK_MINUTES)
        started_blocks = -(-over // block)  # ceiling division
        return min(started_blocks * Ride.PRICE_PER_BLOCK, Ride.MAX_FEE)

    def check_end_time(self, end_time: datetime) -> None:
        if end_time < self._start_time:
            raise ValueError("end time is before start time")

    def finish(self, end_station: Station, end_time: datetime) -> None:
        if not self.is_active:
            raise RideFinishedError("ride is already finished")
        self.check_end_time(end_time)
        self._end_station = end_station
        self._end_time = end_time

    def register_failed_return(self) -> int:
        self._failed_returns += 1
        return self._failed_returns
