"""Demo for the 40-second video: happy, failure and recovery path."""
from datetime import datetime, timedelta

from bikeshare import (
    Bike, Network, ReceiptPrinter, Rider, Station, StationFullError,
)

T0 = datetime(2026, 11, 10, 9, 0)


def at(minutes):
    return T0 + timedelta(minutes=minutes)


def step(text):
    print(f"\n--- {text}")


network = Network(ReceiptPrinter())
chilonzor, yunusobod = Station("Chilonzor", 4), Station("Yunusobod", 2)
network.add_station(chilonzor)
network.add_station(yunusobod)
chilonzor.park_bike(Bike("B1"))
chilonzor.park_bike(Bike("B2"))
yunusobod.park_bike(Bike("B3"))
yunusobod.park_bike(Bike("B4"))          # Yunusobod is now full
ali = Rider("Ali")

step("Start")
network.report()

step("HAPPY PATH: Ali takes a bike at Chilonzor")
ride = network.take_bike(ali, chilonzor, at(0))
print(f"{ali.name} rides {ride.bike.id} ({ride.bike.status.name}); {chilonzor}")

step("FAILURE PATH: return to full Yunusobod, twice (n = 2)")
redirect = None
for attempt, minute in enumerate((20, 21), start=1):
    try:
        network.return_bike(ali, yunusobod, at(minute))
    except StationFullError as error:
        redirect = error.redirect
        print(f"attempt {attempt}: {error}")
print(f"ride still active: {ride.is_active}")

step("RECOVERY PATH: return to the redirected station")
network.return_bike(ali, redirect, at(23))
print(f"{ali.name} paid {ali.total_paid} sum; bike {ride.bike.id} is {ride.bike.status.name}")

step("Manager report")
network.report()
