"""ReceiptPrinter: output helper (no data, only formatting)."""
from __future__ import annotations

from .ride import Ride


class ReceiptPrinter:
    def format(self, ride: Ride) -> str:
        minutes = int(ride.duration.total_seconds() // 60)
        fee = f"{ride.fee:,}".replace(",", " ")
        return f"{ride.start_station.name} → {ride.end_station.name}, {minutes} min, {fee} sum"

    def print(self, ride: Ride) -> None:
        print(self.format(ride))
