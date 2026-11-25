# T069-PS-099 Capstone Submission Report

## 1. Executive Summary
**T069-PS-099 (Freight Exchange Load Matching and Dynamic Truck Pricing Engine)** models an end-to-end B2B road-freight marketplace. It automates dynamic lane pricing, multi-constraint truck eligibility & HOS validation, deterministic ranking & sequential offer timeouts, carrier counter-bidding, trip state enforcement, detention/abort/cancellation penalties, GST/RCM invoicing, 1% TDS compliance, SQLite persistence, structured CSV reporting, and an interactive web dashboard.

## 2. Implemented Capabilities
- **Pricing Engine (BR-01..BR-08, BR-29..BR-30):** Minimum 150 km rule, 200 km supply radius surge bands, 300 km qualifying return-load discount (`-8%`), backhaul-poor surcharge (`+12%`), hazardous (`+15%`) and perishable (`+10%`, `<=6h` window) modifiers, plus optional multi-drop and fuel-index support.
- **Matching & HOS Engine (BR-09..BR-14, BR-26, BR-28):** Capacity, `+1` truck-size tolerance, 150 km pickup radius, hazmat certification, oversize length, 14h daily HOS checks with `second_driver` waiver, rating `>= 3.0` filter, and deterministic `(distance, -rating, truck_id)` ranking with 30-minute offer timeouts.
- **Bidding & Lifecycle (BR-15..BR-21, BR-27):** Counter-offer bands (`<=5%` auto-accept, `5-15%` 60-minute shipper decision, `>15%` reject), full trip state machine, pickup/delivery detention (`6h` free, ceiling rounding, `48h` cap), `>48h` abort compensation, shipper/carrier cancellations, no-show handling, and clamped carrier ratings.
- **Financial Settlement (BR-22..BR-25):** Lane toll cap (`* 1.10`), `6%` platform fee, `5%` GST with RCM flag, and `1%` TDS on trips `> ₹30,000` or crossing `₹1,00,000` annual cumulative payout.
- **Persistence, Validation & UI:** SQLite DDL & repository layer, 6 structured CSV exports, 13-check sample-pack validator, JSON/JSONL command runner, modular test suite, and zero-dependency HTTP dashboard.

## 3. Limitations & Disclosures
- Organizer hidden evaluation inputs/outputs are not supplied in the workspace; all validation checks verify the repository's documented contract and synthetic `sample_data/` pack.
