"""Test name = the 'If' line from the lab text that the test proves."""
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from bikeshare import (
    Bike, BikeStatus, DockOccupiedError, Network, NoActiveRideError, NoBikeError,
    ReceiptPrinter, RepairNotAllowedError, Ride, RideActiveError, Rider, Station,
    StationFullError,
)

T0 = datetime(2026, 11, 10, 9, 0, 0)


def minutes(n, seconds=0):
    return T0 + timedelta(minutes=n, seconds=seconds)


def make_bike(station, bike_id):
    bike = Bike(bike_id)
    station.park_bike(bike)
    return bike


def count_places(network, bike):
    return sum(1 for s in network.stations for d in s.docks if d.bike is bike)


@pytest.fixture
def net():
    return Network(ReceiptPrinter())


# ---------------------------------------------------------------- part 2
def test_if_dock_is_free_bike_is_docked_and_status_is_available():
    station = Station("Chilonzor", 3)
    bike = Bike("B1")
    dock = station.park_bike(bike)
    assert dock.bike is bike
    assert bike.status is BikeStatus.AVAILABLE


def test_if_dock_is_occupied_dock_occupied_error_and_bike_stays_in_use():
    station = Station("Chilonzor", 3)
    dock = station.docks[0]
    dock.park(Bike("B1"))
    second = Bike("B2")
    with pytest.raises(DockOccupiedError):
        dock.park(second)
    assert second.status is BikeStatus.IN_USE


def test_if_outside_code_writes_dock_bike_it_must_fail():
    dock = Station("Chilonzor", 1).docks[0]
    with pytest.raises(AttributeError):
        dock.bike = Bike("B1")


def test_if_outside_code_writes_bike_status_it_must_fail():
    with pytest.raises(AttributeError):
        Bike("B1").status = BikeStatus.AVAILABLE


def test_if_outside_code_appends_to_station_docks_it_must_fail():
    station = Station("Chilonzor", 2)
    with pytest.raises(AttributeError):
        station.docks.append(object())
    assert station.capacity == 2


def test_if_two_station_objects_are_created_each_has_its_own_docks():
    a, b = Station("A", 2), Station("B", 2)
    assert all(da is not db for da in a.docks for db in b.docks)
    make_bike(a, "B1")
    assert len(a) == 1 and len(b) == 0


def test_if_bike_is_in_repair_it_stays_in_the_dock_but_cannot_be_taken():
    station = Station("A", 2)
    bike = make_bike(station, "B1")
    station.send_to_repair("B1")
    assert bike.status is BikeStatus.REPAIR
    assert station.docks[0].bike is bike
    with pytest.raises(NoBikeError):
        station.take_bike()
    assert len(station) == 1


def test_if_bike_is_not_a_docked_free_bike_it_cannot_be_sent_to_repair():
    station = Station("A", 2)
    with pytest.raises(RepairNotAllowedError):
        station.send_to_repair("ghost")        # not docked here
    outside = Bike("B9")                       # IN_USE = outside any dock
    with pytest.raises(RepairNotAllowedError):
        outside.mark_repair()
    bike = make_bike(station, "B1")
    station.send_to_repair("B1")
    with pytest.raises(RepairNotAllowedError):
        station.send_to_repair("B1")           # already in repair


def test_if_print_station_it_shows_name_and_docked_bikes_and_len_counts_them():
    station = Station("Chilonzor", 10)
    for i in range(4):
        make_bike(station, f"B{i}")
    assert str(station) == "Chilonzor: 4/10 bikes"
    assert len(station) == 4
    assert "Chilonzor" in repr(station) and "capacity=10" in repr(station)


def test_if_stations_are_sorted_they_are_ordered_by_free_docks():
    a, b, c = Station("A", 3), Station("B", 3), Station("C", 3)
    make_bike(a, "1"); make_bike(a, "2"); make_bike(a, "3")   # 0 free
    make_bike(b, "4")                                          # 2 free
    make_bike(c, "5"); make_bike(c, "6")                       # 1 free
    assert sorted([b, c, a]) == [a, c, b]


# ---------------------------------------------------------------- part 3
@pytest.mark.parametrize(
    "duration, expected",
    [
        (timedelta(minutes=15), 0),
        (timedelta(minutes=15, seconds=1), 500),
        (timedelta(minutes=20), 500),
        (timedelta(minutes=20, seconds=1), 1000),
        (timedelta(hours=10), 20_000),
    ],
    ids=["15_00_is_0", "15_01_is_500", "20_00_is_500", "20_01_is_1000", "very_long_is_capped_20000"],
)
def test_if_ride_lasted_duration_the_fee_is_calculated_by_ride(duration, expected):
    assert Ride.fee_for(duration) == expected


def test_if_ride_is_finished_the_ride_itself_calculates_the_fee():
    a, b = Station("A", 2), Station("B", 2)
    rider = Rider("Ali")
    ride = Ride(Bike("B1"), rider, a, T0)
    ride.finish(b, minutes(23))
    assert ride.fee == 1000
    assert ride.end_station is b


def test_if_end_time_is_before_start_time_value_error():
    a = Station("A", 1)
    ride = Ride(Bike("B1"), Rider("Ali"), a, T0)
    with pytest.raises(ValueError):
        ride.finish(a, T0 - timedelta(seconds=1))


def test_if_the_fee_numbers_live_outside_ride_move_them():
    src = Path(__file__).resolve().parent.parent / "bikeshare"
    pattern = re.compile(r"(?<![\w.])(500|20_000|20000)(?![\w.])")
    for path in src.glob("*.py"):
        if path.name == "ride.py":
            continue
        code = [ln.split("#")[0] for ln in path.read_text(encoding="utf-8").splitlines()]
        assert not pattern.search("\n".join(code)), f"fee number found in {path.name}"
    ride_text = (src / "ride.py").read_text(encoding="utf-8")
    for number in ("FREE_MINUTES = 15", "BLOCK_MINUTES = 5", "PRICE_PER_BLOCK = 500", "MAX_FEE = 20_000"):
        assert ride_text.count(number) == 1


def test_if_receipt_printer_print_is_called_it_shows_route_minutes_and_fee(capsys):
    a, b = Station("Chilonzor", 2), Station("Yunusobod", 2)
    ride = Ride(Bike("B1"), Rider("Ali"), a, T0)
    ride.finish(b, minutes(23))
    ReceiptPrinter().print(ride)
    assert capsys.readouterr().out.strip() == "Chilonzor → Yunusobod, 23 min, 1 000 sum"


# ---------------------------------------------------------------- part 4
def build(net, full_capacity=2):
    chil = Station("Chilonzor", 4)
    yun = Station("Yunusobod", full_capacity)
    for s in (chil, yun):
        net.add_station(s)
    return chil, yun


def test_if_rider_has_no_active_ride_and_station_has_a_free_bike_new_ride_starts(net):
    chil, yun = build(net)
    bike = make_bike(chil, "B1")
    ali = Rider("Ali")
    ride = net.take_bike(ali, chil, T0)
    assert ride.bike is bike and bike.status is BikeStatus.IN_USE
    assert ali.active_ride is ride and ride.is_active
    assert count_places(net, bike) == 0


def test_if_rider_already_has_an_active_ride_ride_active_error(net):
    chil, _ = build(net)
    make_bike(chil, "B1"); make_bike(chil, "B2")
    ali = Rider("Ali")
    net.take_bike(ali, chil, T0)
    with pytest.raises(RideActiveError):
        net.take_bike(ali, chil, minutes(1))
    assert len(chil) == 1


def test_if_station_has_no_free_bike_no_bike_error(net):
    chil, _ = build(net)
    make_bike(chil, "B1")
    chil.send_to_repair("B1")
    with pytest.raises(NoBikeError):
        net.take_bike(Rider("Ali"), chil, T0)


def test_if_return_without_a_ride_no_active_ride_error(net):
    chil, _ = build(net)
    with pytest.raises(NoActiveRideError):
        net.return_bike(Rider("Ali"), chil, T0)


def fill(station, prefix):
    for i in range(station.capacity):
        make_bike(station, f"{prefix}{i}")


def test_if_station_is_full_on_return_station_full_error_and_ride_clock_keeps_running(net):
    chil, yun = build(net)
    make_bike(chil, "B1")
    fill(yun, "Y")
    ali = Rider("Ali")
    ride = net.take_bike(ali, chil, T0)
    with pytest.raises(StationFullError) as err:
        net.return_bike(ali, yun, minutes(20))
    assert err.value.redirect is None          # first failure: no redirect yet
    assert ride.is_active and ali.active_ride is ride
    assert ride.bike.status is BikeStatus.IN_USE
    assert ride.failed_returns == 1


def test_if_the_same_ride_fails_n_2_times_error_carries_the_redirect(net):
    chil, yun = build(net)
    make_bike(chil, "B1")
    fill(yun, "Y")
    ali = Rider("Ali")
    ride = net.take_bike(ali, chil, T0)
    for minute in (20, 21):
        with pytest.raises(StationFullError) as err:
            net.return_bike(ali, yun, minutes(minute))
    assert ride.failed_returns == 2
    assert err.value.redirect is chil
    assert "Chilonzor" in str(err.value)


def test_if_redirect_has_a_tie_in_free_docks_the_name_a_to_z_wins(net):
    chil, yun = build(net)
    zebra, alpha = Station("Zebra", 3), Station("Alpha", 3)
    net.add_station(zebra); net.add_station(alpha)
    make_bike(chil, "B1")
    fill(yun, "Y")
    ali = Rider("Ali")
    net.take_bike(ali, chil, T0)
    for minute in (20, 21):
        with pytest.raises(StationFullError) as err:
            net.return_bike(ali, yun, minutes(minute))
    # Chilonzor 4 free after take, Alpha 3, Zebra 3 -> Chilonzor most free
    assert err.value.redirect is chil
    fill_chil = [make_bike(chil, f"C{i}") for i in range(4)]  # now Chilonzor full
    with pytest.raises(StationFullError) as err:
        net.return_bike(ali, yun, minutes(22))
    assert err.value.redirect is alpha         # 3 vs 3 -> A before Z
    assert fill_chil


def test_if_rider_returns_the_bike_to_the_redirected_station_ride_closes_fee_charged_receipt_printed(net, capsys):
    chil, yun = build(net)
    bike = make_bike(chil, "B1")
    fill(yun, "Y")
    ali = Rider("Ali")
    ride = net.take_bike(ali, chil, T0)
    for minute in (20, 21):
        with pytest.raises(StationFullError) as err:
            net.return_bike(ali, yun, minutes(minute))
    net.return_bike(ali, err.value.redirect, minutes(23))
    assert not ride.is_active and ali.active_ride is None
    assert ali.total_paid == 1000
    assert bike.status is BikeStatus.AVAILABLE and count_places(net, bike) == 1
    assert "Chilonzor → Chilonzor, 23 min, 1 000 sum" in capsys.readouterr().out
    assert ride in net.history


def test_if_a_bike_is_taken_and_returned_it_is_always_in_exactly_one_place(net):
    chil, yun = build(net)
    bike = make_bike(chil, "B1")
    assert count_places(net, bike) == 1
    ali = Rider("Ali")
    net.take_bike(ali, chil, T0)
    assert count_places(net, bike) == 0
    net.return_bike(ali, yun, minutes(5))
    assert count_places(net, bike) == 1


def test_if_a_docked_bike_is_parked_again_it_fails(net):
    chil, yun = build(net)
    bike = make_bike(chil, "B1")
    with pytest.raises(Exception):
        yun.park_bike(bike)
    assert count_places(net, bike) == 1


def test_if_return_time_is_before_start_the_bike_is_not_parked(net):
    chil, yun = build(net)
    bike = make_bike(chil, "B1")
    ali = Rider("Ali")
    net.take_bike(ali, chil, T0)
    with pytest.raises(ValueError):
        net.return_bike(ali, yun, T0 - timedelta(minutes=1))
    assert count_places(net, bike) == 0 and ali.has_active_ride


def test_if_station_is_not_in_the_network_or_name_repeats_value_error(net):
    chil, _ = build(net)
    with pytest.raises(ValueError):
        net.add_station(Station("Chilonzor", 2))
    with pytest.raises(ValueError):
        net.take_bike(Rider("Ali"), Station("Outsider", 2), T0)


def test_if_network_report_is_called_stations_are_listed_by_free_docks_biggest_first(net, capsys):
    chil, yun = build(net)
    make_bike(chil, "B1")
    fill(yun, "Y")
    net.report()
    lines = capsys.readouterr().out.strip().splitlines()
    assert lines == ["Chilonzor: 3 free docks", "Yunusobod: 0 free docks"]
