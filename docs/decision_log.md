# Decision Log – T069-PS-099

| Date | Decision | Reason / impact |
|---|---|---|
| 2026-11-16 | Use Python 3.10+ and standard library only | Simple deployment; no third-party dependency installation. |
| 2026-11-16 | Keep all sample master and load data in `src/sample_data.py` | Meets request to keep data in Python, with no external data files required. |
| 2026-11-16 | Use `Decimal` for currency and percentage arithmetic | Avoid binary floating-point rounding drift. |
| 2026-11-16 | Add percentage adjustments to base price before one final rupee rounding | Makes adjustment interaction deterministic and auditable. |
| 2026-11-16 | Strictly apply surge thresholds (`>`), inclusive 150 km eligibility and exact 1-hour free cancellation | Matches supplied edge-case wording. |
| 2026-11-16 | Document missing toll table and response-event details as assumptions | Those schemas were not included in the problem statement. |
