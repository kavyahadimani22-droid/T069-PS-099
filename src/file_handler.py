import json
from pathlib import Path

def run_command_file(engine,path):
    commands=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(commands,list): raise ValueError("Command file must be a JSON array")
    for c in commands:
        op=c["op"].upper()
        if op=="MATCH": engine.match_cycle()
        elif op=="ADVANCE": engine.advance(c["minutes"])
        elif op=="ACCEPT": engine.respond_offer(c["load_id"],True)
        elif op=="DECLINE": engine.respond_offer(c["load_id"],False)
        elif op=="COUNTER": engine.counter(c["trip_id"],c["amount"])
        elif op=="SHIPPER_DECISION": engine.shipper_counter_decision(c["trip_id"],c["accept"])
        elif op=="EVENT": engine.event(c["trip_id"],c["event"],**c.get("data",{}))
        else: raise ValueError(f"Unknown command {op}")
