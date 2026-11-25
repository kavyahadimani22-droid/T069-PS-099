# SQLite Integration Runbook (T069-PS-099)

T069-PS-099 uses Python's built-in `sqlite3` engine with `PRAGMA foreign_keys = ON` so relational persistence works immediately with zero external server setup.

## Schema Files (Execution Order)
1. `app/database/schema.sql` &mdash; `shippers`, `carriers`, `trucks`, `lanes`, `toll_caps`, `poor_cities`
2. `app/database/operations_schema.sql` &mdash; `loads`, `trips`, `offer_history`, `rejection_records`
3. `app/database/settlement_schema.sql` &mdash; `settlements`, `shipper_invoices`, `audit_logs`

## Verification Commands
```powershell
# 1. Verify DDL table and column contracts in memory
python verify_database_schema.py

# 2. Run disposable acceptance test on a temporary SQLite DB
python run_sqlite_acceptance_demo.py

# 3. Persist the full sample-pack run to outputs/freight_exchange.db
python run_sample_pack.py
```
