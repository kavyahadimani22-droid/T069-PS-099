# T069-PS-099 Official-Style Sample Data Pack

This directory contains a complete, self-contained CSV/JSONL freight marketplace dataset designed to exercise business rules **BR-01 through BR-28** in a single reproducible run.

## Files
- `lanes.csv`: Symmetric city-to-city distances (km).
- `toll_caps.csv`: Lane toll caps (actual toll capped at `cap * 1.10`).
- `backhaul_poor_cities.csv`: Destination cities receiving the `+12%` backhaul-poor surcharge.
- `shippers.csv`: Registered shippers (mix of GST-registered and non-GST).
- `carriers.csv`: Registered carriers (mix of ratings, single/dual driver, and cumulative payouts).
- `trucks.csv`: Fleet across LCV, 17FT, 22FT, 32FT_MXL, and TRAILER categories.
- `loads.csv`: Multi-scenario loads (minimum 150 km, return-load discount, hazardous, perishable, oversize, backhaul-poor).
- `commands.jsonl`: Ordered lifecycle events (match, accept, counter-bid, deliver, late delivery, shipper cancel, carrier cancel, abort, settle).

## Run
```powershell
python run_sample_pack.py
python validate_sample_pack_outputs.py
```
