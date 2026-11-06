from decimal import Decimal
def update_rating(carrier,outcome):
    delta={"ON_TIME":Decimal(".05"),"LATE_OVER_4H":Decimal("-.1"),"CANCELLATION":Decimal("-.2")}
    if outcome not in delta:raise ValueError("Unknown outcome")
    carrier.rating=min(Decimal("5.0"),max(Decimal("1.0"),carrier.rating+delta[outcome]));return carrier.rating
def is_rankable(carrier):return carrier.rating>=3
