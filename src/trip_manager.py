"""Trip lifecycle facade; event validation and orchestration live in FreightEngine."""
from src.models import TripState

VALID_TRANSITIONS = {
    TripState.MATCHED: {TripState.AT_PICKUP, TripState.CANCELLED},
    TripState.AT_PICKUP: {TripState.LOADED, TripState.CANCELLED, TripState.ABORTED},
    TripState.LOADED: {TripState.IN_TRANSIT},
    TripState.IN_TRANSIT: {TripState.DELIVERED},
    TripState.DELIVERED: {TripState.SETTLED},
}
def validate_transition(current, target):
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid trip transition: {current.value} -> {target.value}")
    return True
