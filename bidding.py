from datetime import timedelta
from decimal import Decimal
from .utils import dec
def evaluate_counteroffer(recommended,counter):
    r,c=dec(recommended),dec(counter)
    if r<=0 or c<r:return "REJECTED"
    pct=(c-r)/r
    if pct>Decimal(".15"):return "REJECTED"
    return "AUTO_ACCEPTED" if pct<=Decimal(".05") else "SHIPPER_RESPONSE_REQUIRED"
def offer_expired(sent_at,response_at=None):
    return response_at is None or response_at>sent_at+timedelta(minutes=30)
def counter_expired(sent_at,response_at=None):
    return response_at is None or response_at>sent_at+timedelta(minutes=60)
def next_offer(proposals,responded):
    return next((p for p in proposals if p.truck_id not in responded),None)
