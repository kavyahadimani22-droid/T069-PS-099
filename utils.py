from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
def dec(v): return Decimal(str(v or 0))
def cash(v): return dec(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
def dt(v): return datetime.fromisoformat(v)
def ceil_int(v):
    v=dec(v)
    return int(v) if v == v.to_integral_value() else int(v)+1
