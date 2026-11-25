"""JSON and JSONL command dispatcher for FreightEngine workflows."""

import json
from decimal import Decimal
from pathlib import Path

from app.models.entities import Carrier, Load, Shipper, Truck
from app.services.exceptions import RuleError


def _parse_commands(path: Path) -> list[dict]:
    """Load either a JSON array file (.json) or line-delimited JSONL file (.jsonl)."""
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    if raw.startswith("["):
        data = json.loads(raw)
        if not isinstance(data, list):
            raise RuleError("JSON command file must contain a list of command objects")
        return data
    commands = []
    for idx, line in enumerate(raw.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            commands.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise RuleError(f"Invalid JSON on line {idx}: {exc}") from exc
    return commands


def execute_command(engine, cmd: dict) -> dict:
    """Execute one command dictionary on FreightEngine and return a structured result."""
    op = (cmd.get("op") or cmd.get("command") or "").upper()
    if not op:
        raise RuleError("Command missing 'op' field")

    if op == "REGISTER_SHIPPER":
        s = Shipper(cmd["id"], cmd["name"], bool(cmd.get("gst_registered", False)))
        engine.register_shipper(s)
        return {"op": op, "status": "OK", "id": s.id}

    if op == "REGISTER_CARRIER":
        c = Carrier(
            cmd["id"],
            cmd["name"],
            rating=Decimal(str(cmd.get("rating", "4.0"))),
            annual_payout=Decimal(str(cmd.get("annual_payout", "0"))),
            second_driver=bool(cmd.get("second_driver", False)),
            active=bool(cmd.get("active", True)),
        )
        engine.register_carrier(c)
        return {"op": op, "status": "OK", "id": c.id}

    if op == "REGISTER_TRUCK":
        t = Truck(
            cmd["id"],
            cmd["carrier_id"],
            cmd["truck_type"],
            Decimal(str(cmd["capacity_tonnes"])),
            Decimal(str(cmd["length_ft"])),
            cmd["city"],
            available_from=int(cmd.get("available_from", 0)),
            hours_used=Decimal(str(cmd.get("hours_used", "0"))),
            haz_certified=bool(cmd.get("haz_certified", False)),
            active=bool(cmd.get("active", True)),
        )
        engine.register_truck(t)
        return {"op": op, "status": "OK", "id": t.id}

    if op == "POST_LOAD":
        load = Load(
            cmd["id"],
            cmd["shipper_id"],
            cmd["origin"],
            cmd["destination"],
            Decimal(str(cmd["weight_tonnes"])),
            cmd["truck_type"],
            int(cmd["pickup_start"]),
            int(cmd["pickup_end"]),
            material=cmd.get("material", "GENERAL"),
            length_ft=Decimal(str(cmd.get("length_ft", "0"))),
            extra_stops=int(cmd.get("extra_stops", 0)),
        )
        price = engine.post_load(load)
        return {"op": op, "status": "OK", "id": load.id, "recommended_price": str(price["recommended_price"])}

    if op == "MATCH":
        engine.match_cycle()
        return {"op": op, "status": "OK", "minute": engine.now}

    if op == "ACCEPT":
        res = engine.respond_offer(cmd["load_id"], True, cmd.get("minute"))
        return {"op": op, "status": res, "load_id": cmd["load_id"]}

    if op == "DECLINE":
        res = engine.respond_offer(cmd["load_id"], False, cmd.get("minute"))
        return {"op": op, "status": res, "load_id": cmd["load_id"]}

    if op == "ADVANCE":
        engine.advance(cmd["minutes"])
        return {"op": op, "status": "OK", "minute": engine.now}

    if op == "COUNTER":
        res = engine.counter(cmd["trip_id"], cmd["amount"])
        return {"op": op, "status": res, "trip_id": cmd["trip_id"]}

    if op == "SHIPPER_DECISION":
        res = engine.shipper_counter_decision(cmd["trip_id"], bool(cmd["accept"]))
        return {"op": op, "status": res, "trip_id": cmd["trip_id"]}

    if op == "EVENT":
        state = engine.event(cmd["trip_id"], cmd["event"], **cmd.get("data", {}))
        return {"op": op, "status": "OK", "trip_id": cmd["trip_id"], "state": state.value}

    raise RuleError(f"Unsupported command op: {op}")


def run_commands(engine, commands: list[dict], stop_on_error: bool = False) -> list[dict]:
    """Run an in-memory list of commands and return per-command execution records."""
    results: list[dict] = []
    for index, cmd in enumerate(commands, start=1):
        try:
            outcome = execute_command(engine, cmd)
            results.append({"seq": index, **outcome})
        except Exception as exc:
            if stop_on_error:
                raise
            results.append({"seq": index, "op": cmd.get("op", ""), "status": "ERROR", "error": str(exc)})
    return results


def run_command_file(engine, path: str | Path, stop_on_error: bool = False) -> list[dict]:
    """Load and execute commands from a JSON or JSONL command file."""
    commands = _parse_commands(Path(path))
    return run_commands(engine, commands, stop_on_error=stop_on_error)
