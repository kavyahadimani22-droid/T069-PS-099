# Sample Data Pack Documentation (`sample_data/`)

The `sample_data/` pack exercises all core freight marketplace rules in one reproducible workflow:

## Planted Scenarios

| Load / Entity | Scenario Covered | Rules Verified |
|---|---|---|
| `LD-001` (Bengaluru &rarr; Chennai, 17FT) | 3 open Chennai&rarr;Bengaluru return loads (`LD-009`..`LD-011`) give `-8%` discount; toll capped at `700 * 1.10 = 770`; GST + RCM flag `True` | BR-05, BR-22, BR-24 |
| `LD-002` (Mumbai &rarr; Pune, LCV, PERISHABLE) | Perishable `+10%`, pickup window 240 min (&le;6h); `CAR-002` crosses ₹1,00,000 cumulative payout &rarr; 1% TDS triggered | BR-08, BR-25 |
| `LD-003` (Bengaluru &rarr; Delhi, 32FT_MXL, HAZARDOUS) | Delhi backhaul-poor (`+12%`) + Hazardous (`+15%`) + single-trip payout &gt;₹30,000 &rarr; 1% TDS | BR-06, BR-07, BR-25 |
| `LD-004` (Mumbai &rarr; Bengaluru, 22FT) | Carrier counter `+8%` (`₹33,869`) requires shipper decision, accepted; delivered `6h` late (`>4h`) &rarr; rating `-0.1` | BR-15, BR-16, BR-27 |
| `LD-005` (Bengaluru &rarr; Mysuru, LCV) | Distance `145 km` billed as `150 km`; shipper cancels at minute `90` &rarr; `₹1,000` fee | BR-01, BR-20 |
| `LD-006` (Pune &rarr; Hyderabad, TRAILER, OVERSIZE) | `36 ft` load matched to `40 ft` trailer; carrier aborts at `54h` detention &rarr; `48h` capped detention (`₹38,400`) + 50% base compensation | BR-09, BR-18, BR-19 |
| `LD-007` (Bengaluru &rarr; Hyderabad, 17FT) | Carrier cancels after acceptance &rarr; `₹2,000` fee and rating `-0.2` | BR-21, BR-27 |
| `TRK-004` / `CAR-004` | Rating `2.8` (`<3.0`) excluded from ranking | BR-28 |
| `TRK-010` / `CAR-002` | Single driver with `12h` used (`2h` left) fails HOS checks | BR-12, BR-26 |
