# Five-Minute Placement & Faculty Demo Guide (T069-PS-099)

Use this step-by-step script when presenting your capstone project to faculty or placement interviewers.

## 1. Show Clean Architecture & Verification (1 min)
Run the automated test suite and SQLite schema contract verifier:
```powershell
python -m unittest discover -s tests -v
python verify_database_schema.py
```
Highlight:
- Modular separation into `models/`, `services/`, `repositories/`, `database/`, `commands/`, and `web/`.
- Zero mandatory external dependencies (pure Python 3.10+ standard library).

## 2. Run the Full Sample Data Pack & Output Validator (1.5 min)
```powershell
python run_sample_pack.py
python validate_sample_pack_outputs.py
```
Open `outputs/` and show the 6 generated CSVs (`price_breakdowns.csv`, `trips.csv`, `settlements.csv`, `shipper_invoices.csv`, `carrier_ratings.csv`, `rejections.csv`) plus `freight_exchange.db`.

Point out 3 concrete scenarios in the output:
1. `LD-001` gets a `-8%` return-load discount (`BR-05`), toll capped at `₹770` (`BR-22`), and `RCM=True` (`BR-24`).
2. `LD-002` triggers **cumulative annual TDS** (`BR-25`) when `CAR-002` crosses `₹1,00,000`.
3. `LD-006` shows `>48h` pickup detention abort (`BR-19`) with `48h` capped detention + `50%` base compensation.

## 3. Launch the Interactive Web Dashboard (2 min)
```powershell
python run_dashboard.py
```
Open `http://127.0.0.1:8069` in your browser:
- Show the top KPI cards (Loads, Settled Trips, Freight Volume, 6% Platform Revenue, 1% TDS).
- Use the **Interactive Dynamic Pricing Simulator** live in front of the panel (e.g., switch destination to `Delhi` and material to `HAZARDOUS` to show `+12%` backhaul-poor + `+15%` hazardous modifiers, or add `extra_stops` / `fuel_index_pct` for BR-29/30).
- Scroll to **Truck Eligibility Rejection Audit** to explain why low-rated (`<3.0`) and HOS-violating trucks were automatically filtered out.

## 4. Mention Focused Scenario Demos (30 sec)
If asked about specific edge cases, show you also have standalone demo scripts:
- `python run_pricing_demo.py`
- `python run_matching_bidding_demo.py`
- `python run_detention_settlement_demo.py`
- `python run_cancellation_abort_demo.py`
