# Command File Format Specification (JSON & JSONL)

`app/commands/command_processor.py` supports both:
- **JSON array files** (`.json`), e.g. `examples/commands_basic.json`
- **Line-delimited JSONL files** (`.jsonl`), e.g. `sample_data/commands.jsonl`

## Supported Operations (`op`)

| `op` | Required Fields | Optional Fields | Description |
|---|---|---|---|
| `REGISTER_SHIPPER` | `id`, `name` | `gst_registered` (bool) | Register a shipper |
| `REGISTER_CARRIER` | `id`, `name` | `rating`, `annual_payout`, `second_driver`, `active` | Register a carrier |
| `REGISTER_TRUCK` | `id`, `carrier_id`, `truck_type`, `capacity_tonnes`, `length_ft`, `city` | `available_from`, `hours_used`, `haz_certified`, `active` | Register a truck |
| `POST_LOAD` | `id`, `shipper_id`, `origin`, `destination`, `weight_tonnes`, `truck_type`, `pickup_start`, `pickup_end` | `material`, `length_ft`, `extra_stops` | Post & price a load |
| `MATCH` | &mdash; | &mdash; | Price open loads, filter/rank trucks, send offers |
| `ACCEPT` | `load_id` | `minute` | Carrier accepts active offer |
| `DECLINE` | `load_id` | `minute` | Carrier declines offer (advances to next truck) |
| `ADVANCE` | `minutes` | &mdash; | Advance simulation clock & process timeouts |
| `COUNTER` | `trip_id`, `amount` | &mdash; | Submit carrier counter-offer |
| `SHIPPER_DECISION` | `trip_id`, `accept` | &mdash; | Shipper accepts/rejects pending 5–15% counter |
| `EVENT` | `trip_id`, `event` | `data` (dict) | Trigger `AT_PICKUP`, `LOADED`, `IN_TRANSIT`, `DELIVERED`, `SETTLE`, `CANCEL_SHIPPER`, `CANCEL_CARRIER`, `NO_SHOW`, `ABORT` |

## Run Commands
```powershell
python run_commands.py examples/commands_full_lifecycle.jsonl --output outputs/command_results.jsonl
```
