# T069-PS-099 Design Document

## 1. Purpose
Implement a modular, persistent freight marketplace engine covering shipper/carrier/truck registration, load posting, dynamic pricing, eligibility filtering & ranking, bidding, trip lifecycle state transitions, financial settlement (toll caps, GST/RCM, platform fee, TDS), carrier ratings, CSV reporting, and interactive dashboard visualization.

## 2. Architecture Overview
The application follows a clean layered design under `app/`:
- `app/models/entities.py`: Dataclasses for `Shipper`, `Carrier`, `Truck`, `Load`, `Trip`, and `State`.
- `app/services/`: Single-responsibility domain modules:
  - `pricing_service.py`: BR-01..BR-08 plus optional BR-29 (multi-drop) and BR-30 (fuel index).
  - `matching_service.py`: BR-09..BR-13, BR-26, BR-28 eligibility & deterministic ranking.
  - `bidding_service.py`: BR-15..BR-16 counter-offer evaluation.
  - `trip_lifecycle_service.py`: BR-17..BR-21, BR-27 detention, cancellation fees, ratings.
  - `settlement_service.py`: BR-22..BR-25 toll caps, 6% platform fee, 5% GST/RCM, 1% TDS.
  - `reporting_service.py`: Text summary & 6 structured CSV exports.
  - `freight_engine.py`: Stateful orchestrator (`FreightEngine`).
  - `sample_loader.py`: Quick demo builder and CSV sample-data loader.
- `app/database/` & `app/repositories/`: SQLite DDL schemas (`schema.sql`, `operations_schema.sql`, `settlement_schema.sql`) and `FreightRepository`.
- `app/commands/command_processor.py`: JSON and JSONL command execution engine.
- `app/web/dashboard_server.py`: Zero-dependency live web dashboard (`http://127.0.0.1:8069`).

## 3. Diagrams
- [Entity-Relationship Diagram](diagrams/er_diagram.md)
- [Class & Service Architecture](diagrams/class_diagram.md)
- [Trip Lifecycle State Machine](diagrams/state_diagrams.md)
- [Matching & Bidding Sequence](diagrams/sequence_diagram.md)

## 4. Business Rule Register (BR-01 to BR-30)
See [BR-to-Test Traceability Matrix](br_test_matrix.md) for the complete mapping from every rule to its implementation and automated verification test.

## 5. Key Boundary & Edge Conditions
- 149 km charges as 150 km (`MIN_KM = 150`).
- Demand/supply ratio `== 1.5` has no surge; `== 0.5` has no discount (`>1.5` and `<0.5` are strict).
- Truck-to-origin distance `== 150 km` is eligible; `151 km` is rejected.
- Counter-offer `== +5%` is auto-accepted; `== +15%` requires shipper decision; `> +15%` is rejected.
- Detention of 6h 1m charges 1 billable hour; capped at 48 hours per detention period.
- Shipper cancellation `<= 60 min` is free; `<= 360 min` is ₹1,000; `> 360 min` is 10% of base freight.
- Remaining driver hours exact-equal to `distance/40 + 2` buffer is eligible.
- Annual cumulative payout crossing ₹1,00,000 triggers 1% TDS on the crossing trip.
