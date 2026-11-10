# Design: Bike sharing network (class discovery, CRC cards)

Paper/markdown only, made before the code. Source: requirement text from Lecture 4.

## 1. Nouns from the requirement text

| Noun (from the text) | Verdict | Why |
|---|---|---|
| Tashkent bike network | **class `Network`** | has data (stations, ride history) and behaviour (runs take/return, manager report) |
| station | **class `Station`** | has data (name, docks) and behaviour (park, take, count free docks) |
| dock | **class `Dock`** | has data (the bike inside) and behaviour (holds at most one bike) |
| number of docks | attribute `Station.capacity` | only a value |
| bike | **class `Bike`** | has data (id, status) and behaviour (legal status changes) |
| rider / user | **merge → class `Rider`** | two names for one thing; has data (active ride, total paid) and behaviour (one active ride only) |
| ride | **class `Ride`** | *event with data* (the noun you cannot touch). **`Ride.fee_for` / `Ride.fee` owns the money rule** |
| start station, end station | attributes of `Ride` | links to `Station` |
| times | attributes of `Ride` (`start_time`, `end_time`) | only values |
| 15 minutes, 5 minutes, 500 sum, 20 000 sum | constants in `Ride` | only values, written once (DRY) |
| fee, money | attribute / `int` sum | only a value |
| repair | value of `Bike.status` (`REPAIR`) | only a value |
| free docks | derived value `Station.free_docks` | computed, not stored |
| manager | **actor** | outside the program, only reads the report |
| the app | system boundary | not a class |

Result: **6 classes**: `Network`, `Station`, `Dock`, `Bike`, `Ride`, `Rider`.

Extra, not counted as a domain class: `ReceiptPrinter` (named in the lab for the receipt). It has no data, only formatting, and it keeps `Network` under 4 responsibilities.

### Vague words: questions for the customer
- "A bike sent to repair": **who** sends it (manager? technician?) and **when** does it come back? *(Assumed: any code with the station can call `send_to_repair` / `finish_repair`.)*
- "started 5 minutes": is the clock counted per second? *(Assumed yes: 15:01 already starts the next block.)*
- "any free dock": does the rider choose the dock? *(Assumed no: the station picks the first free dock.)*
- "A station is full and the rider cannot return": how many tries before the app helps? *(Given in the lab: n = 2.)*

## 2. CRC cards

| Class | Responsibilities | Collaborators |
|---|---|---|
| **Bike** | 1. know its id and status (AVAILABLE / IN_USE / REPAIR) 2. allow only legal status changes | Dock |
| **Dock** | 1. hold at most one bike 2. park / release a bike together with its status change 3. send the docked bike to repair and back | Bike |
| **Station** | 1. own its docks (created inside, fixed number) 2. park a bike in a free dock / hand out an available bike 3. answer free docks, docked bikes, text form 4. order itself by free docks | Dock, Bike |
| **Ride** | 1. hold ride data (bike, rider, start/end station, times) 2. **calculate the fee (money rule)** 3. finish itself and refuse end before start 4. **count failed returns** | Bike, Rider, Station |
| **Rider** | 1. know the active ride (max one) 2. start / finish a ride 3. remember how much was paid | Ride |
| **Network** | 1. register stations, keep ride history 2. run **take bike** 3. run **return bike** (including the redirect station) 4. manager report | Station, Rider, Ride, ReceiptPrinter |
| *ReceiptPrinter* (helper) | 1. format and print a ride receipt | Ride |

No card has more than 4 responsibilities, so no split is needed. (`Station` and `Network` are exactly at 4. Printing was moved to `ReceiptPrinter` to keep `Network` at 4.)

## 3. Scenario read aloud: "rider returns bike to a full station"

| Step | Owner |
|---|---|
| 1. Rider taps "Return" at station Y | `Network.return_bike` |
| 2. Find the rider's active ride | `Rider.active_ride` |
| 3. Check the time is not before the start | `Ride.check_end_time` |
| 4. Look for a free dock at Y | `Station.park_bike` → `Dock.is_free` |
| 5. No free dock → error | `Station` raises `StationFullError` |
| 6. Count the failed attempt for this ride | **`Ride.register_failed_return`** (see rounds below) |
| 7. Decide whether the error gets a redirect (count ≥ n = 2) | `Network` |
| 8. Choose the station with most free docks (tie → A–Z) | `Network._best_redirect` |
| 9. Ride clock keeps running, bike stays IN_USE | `Ride` (still active), `Bike` |
| 10. Rider returns to the redirected station: ride closes, fee, receipt | `Ride.finish`, `Ride.fee`, `Rider.finish_ride`, `ReceiptPrinter` |

### Steps that had no owner
- **Step 6, "count failed attempts".** Round 1: no card owned it. I tried `Rider`, but a counter on the rider must be reset on every new ride. Round 2: tried `Network` with a dictionary ride → count, but that duplicates ride data and could go stale. Still no clean owner after *n* = 2 rounds, so by **Information Expert** it goes to **`Ride`**: the failed attempts belong to exactly one ride, `Ride` has that data, and the counter dies with the ride.
- **Step 8, "most free docks".** Only `Network` knows all stations, so `Network` is the expert. `Station` knows only itself.

## 4. Rules and where they live

| Rule | Owner |
|---|---|
| A dock holds at most one bike | `Dock.park` |
| A bike is in exactly one place | `Dock.park` / `Dock.take_bike` change the slot and the status together; `Bike` rejects illegal changes |
| Only a docked free bike can be repaired | `Bike.mark_repair` |
| Repair bike cannot be taken | `Bike.mark_taken`; `Station.take_bike` skips it |
| One active ride per rider | `Rider.start_ride` |
| Fee, 15 / 5 / 500 / 20 000 | `Ride` (constants written once) |
| Redirect after n = 2 failures | counter in `Ride`, decision in `Network` |
