# Bike sharing network: classes, relationships and encapsulation

Console bike sharing app (Tashkent), Python 3.10+. Laboratory work, Lecture 4.
No files, no database, no threads.

```
bikeshare/   bike.py  dock.py  station.py  ride.py  rider.py  network.py  receipt.py  errors.py
tests/       test_bike_sharing.py      (test name = the "If" line it proves)
docs/        design.md                 (nouns + CRC cards)
demo.py      the exact scenario of the video
```

Run:

```bash
pip install -r requirements.txt
python demo.py
pytest -v
```

## Demo video (max 40 s)

<details>
<summary>Click to expand / collapse the demo video</summary>

<!-- TODO: replace the line below with your own recording of `python demo.py` and `pytest -v` -->
[demo video: add link or drag the .mp4 here]

Scenario step by step (`python demo.py`):

1. **Happy path:** Ali takes bike B1 at Chilonzor, bike is `IN_USE`.
2. **Failure path:** Ali tries to return it to the full Yunusobod. Attempt 1: `StationFullError`. Attempt 2 (n = 2 exhausted): the error now names the redirect station Chilonzor. The ride is still active.
3. **Recovery path:** Ali returns the bike to Chilonzor, the receipt is printed, and the fee is charged.
4. Manager report (optional part).
5. `pytest -v`.

Output of `python demo.py`:

```text
--- Start
Chilonzor: 2 free docks
Yunusobod: 0 free docks

--- HAPPY PATH: Ali takes a bike at Chilonzor
Ali rides B1 (IN_USE); Chilonzor: 1/4 bikes

--- FAILURE PATH: return to full Yunusobod, twice (n = 2)
attempt 1: Station Yunusobod is full
attempt 2: Station Yunusobod is full; return the bike to Chilonzor instead
ride still active: True

--- RECOVERY PATH: return to the redirected station
Chilonzor → Chilonzor, 23 min, 1 000 sum
Ali paid 1000 sum; bike B1 is AVAILABLE

--- Manager report
Chilonzor: 2 free docks
Yunusobod: 0 free docks
```

</details>

### `pytest -v`

<!-- TODO: paste your real `pytest -v` output here (run it on your machine) -->
```text
(paste the output of: pytest -v)
```

## Optional parts (done)
- `sorted(stations)` orders stations by free docks (`Station.__lt__`).
- `network.report()` prints stations by free docks, biggest first (tie → name A–Z).

## Relationships table

| Pair | Relationship | Multiplicity | Proof (file:line) |
|---|---|---|---|
| Station → Dock | **composition** | 1 — 1..* | `bikeshare/station.py:17` (docks created inside `__init__`) |
| Dock → Bike | **aggregation** | 1 — 0..1 | `bikeshare/dock.py:29` (bike comes from outside and is kept) |
| Network → Station | **aggregation** | 1 — 0..* | `bikeshare/network.py:32` (station comes from outside) |
| Network → Ride | **composition** | 1 — 0..* | `bikeshare/network.py:39` (created inside) and `:41` (kept in history) |
| Network → ReceiptPrinter | **aggregation** | 1 — 1 | `bikeshare/network.py:17` (printer is passed in) |
| Rider → Ride | **association** | 1 — 0..1 (active ride) | `bikeshare/rider.py:37` |
| Ride → Bike | **association** | * — 1 | `bikeshare/ride.py:23` |
| Ride → Rider | **association** | * — 1 | `bikeshare/ride.py:24` |
| Ride → Station (start) | **association** | * — 1 | `bikeshare/ride.py:25` |
| Ride → Station (end) | **association** | * — 0..1 (None while active) | `bikeshare/ride.py:93` |
| StationFullError → Station (redirect) | **association** | * — 0..1 | `bikeshare/errors.py:51` |
| Station → Bike | **dependency** | (parameter only) | `bikeshare/station.py:35` (`park_bike(self, bike)`) |
| Network → Rider | **dependency** | (parameter only) | `bikeshare/network.py:34` and `:44` |
| ReceiptPrinter → Ride | **dependency** | (parameter only) | `bikeshare/receipt.py:13` |

### Lifetime tests
- Station ◆ Dock: *If I delete the Station, do its Docks disappear?* **Yes.** Docks are created inside the station and nobody else holds them.
- Network ◆ Ride: *If I delete the Network, does its ride history disappear?* **Yes.** The network created the rides and keeps the history. (A `Rider` points to a ride only while it is active.)
- Dock ◇ Bike: *If I delete the Dock, does the Bike disappear?* **No.** The bike was created outside and lives on.
- Network ◇ Station: *If I delete the Network, do the Stations disappear?* **No.** They were created outside and can be used again.
- Network ◇ ReceiptPrinter: *If I delete the Network, does the printer disappear?* **No.** It was passed in.

### Multiplicities and what enforces them
- Station has **1..\*** docks: `bikeshare/station.py:13` rejects capacity < 1.
- Dock holds **0..1** bike: `bikeshare/dock.py:27` raises `DockOccupiedError`.
- A Bike is in **at most one** dock: this was **not enforced at first** (the same bike object could be parked in two docks). Now `Bike.mark_parked` (`bikeshare/bike.py:39`) refuses a bike that is not `IN_USE`.
- Station names are **unique** in a Network: `bikeshare/network.py:31`. A station used with a Network must be one it registered: `bikeshare/network.py:79`.
- Rider has **0..1** active ride: `bikeshare/rider.py:36`.
- Not enforced on purpose: the number of rides in the network history is unbounded (0..\*), because the lab has no limit.

## "A bike is in exactly one place"

```text
A bike is always in exactly one place: in one dock (AVAILABLE or REPAIR) or in one
active ride (IN_USE). Never in two docks, never in a dock and a ride at once.

How it is held:
1. The bike's status says where it is. A new bike starts IN_USE (outside every dock).
2. Only Dock moves a bike, and it changes the slot and the status in one method.
   Dock.park: checks the dock is free, calls bike.mark_parked() (IN_USE -> AVAILABLE),
   then stores the bike. Dock.take_bike: calls bike.mark_taken() (AVAILABLE -> IN_USE),
   then empties the slot.
3. Bike refuses illegal moves. Parking a bike that is already docked raises
   BikeAlreadyDockedError, so the same bike cannot sit in two docks. Taking a REPAIR bike
   raises BikeNotAvailableError.
4. dock.bike and bike.status are read-only properties, and station.docks is a tuple copy,
   so outside code cannot move a bike by writing a field.
5. Network.return_bike checks the time first and parks the bike before it closes the ride.
   If parking fails (full station), the bike stays IN_USE and the ride stays active.
   The tests count the docks that hold the bike: 1 after parking, 0 while it is in a ride.
```
