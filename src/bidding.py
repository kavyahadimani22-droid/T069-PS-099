from decimal import Decimal
from config import MAX_COUNTER_RATE, AUTO_ACCEPT_COUNTER_RATE, OFFER_RESPONSE_MINUTES, COUNTER_RESPONSE_MINUTES

class BiddingEngine:
    def evaluate_counter(self, recommended, counter_amount, elapsed_minutes):
        counter_amount = Decimal(counter_amount)
        delta = (counter_amount - recommended) / recommended if recommended else Decimal("0")
        if delta > MAX_COUNTER_RATE:
            return "REJECTED"
        if delta <= AUTO_ACCEPT_COUNTER_RATE:
            return "AUTO_ACCEPTED"
        if elapsed_minutes > COUNTER_RESPONSE_MINUTES:
            return "LAPSED"
        return "SHIPPER_DECISION_REQUIRED"

    def offer_expired(self, elapsed_minutes):
        return elapsed_minutes > OFFER_RESPONSE_MINUTES
