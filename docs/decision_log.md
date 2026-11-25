# Decision Log (T069-PS-099)

1. **Zero-dependency Python 3.10+ core:** Standard library (`decimal`, `dataclasses`, `csv`, `json`, `sqlite3`, `http.server`, `unittest`) powers the entire engine, persistence layer, CSV exports, and web dashboard so any evaluator can run it without third-party setup.
2. **Exact financial arithmetic:** All monetary, percentage, weight, and HOS calculations use `Decimal` with `ROUND_HALF_UP` whole-rupee rounding (and `ROUND_CEILING` for detention intervals).
3. **Additive percentage pricing:** Surge, return-load discount, backhaul-poor surcharge, material surcharge, and optional fuel-index adjustments are summed additively on base freight before a single whole-rupee rounding step.
4. **Strict comparison boundaries:** Surge thresholds (`>4`, `>2.5`, `>1.5`, `<0.5`), TDS thresholds (`>30,000`, `>1,00,000`), and late-delivery penalty (`>4h`) use strict inequalities as specified.
5. **Truck size order:** `LCV < 17FT < 22FT < 32FT_MXL < TRAILER`; exact match or one category larger is eligible while billing remains at the requested truck type's rate.
6. **Sequential top-3 offer queue:** Top 3 ranked trucks are queued per load; acceptance, decline, and 30-minute offer timeouts are explicit commands/events.
7. **SQLite persistence:** Selected SQLite (`app/database/*.sql`) with foreign-key enforcement enabled so evaluators get full relational DDL and persistence verification without needing a separate MySQL server.
8. **Optional stretch goals (BR-29, BR-30):** Multi-drop (`extra_stops`) and monthly fuel-price index (`fuel_index_pct`) default to `0` so baseline evaluation outputs remain unchanged unless explicitly enabled.
9. **Evaluator parity note:** Since organizer-provided hidden evaluation datasets are not bundled, `sample_data/` provides a comprehensive synthetic benchmark covering BR-01 through BR-28.
