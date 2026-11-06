from .models import State
ALLOWED={State.MATCHED:{State.AT_PICKUP,State.CANCELLED},State.AT_PICKUP:{State.LOADED,State.CANCELLED,State.ABORTED},State.LOADED:{State.IN_TRANSIT,State.CANCELLED},State.IN_TRANSIT:{State.DELIVERED},State.DELIVERED:{State.SETTLED},State.SETTLED:set(),State.CANCELLED:set(),State.ABORTED:set()}
def transition(trip,new_state,event_time=None):
    new_state=State(new_state)
    if new_state not in ALLOWED[trip.state]:raise ValueError(f"Invalid transition {trip.state.value} -> {new_state.value}")
    trip.state=new_state;return trip
