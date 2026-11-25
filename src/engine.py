from decimal import Decimal
from src.models import State, Trip
from src.rules import *
from config import RATES

class FreightEngine:
    def __init__(self, distances, poor_cities=None, toll_caps=None):
        self.distances=distances; self.poor_cities=set(poor_cities or [])
        self.toll_caps=toll_caps or {}
        self.shippers={}; self.carriers={}; self.trucks={}; self.loads={}; self.trips={}
        self.logs=[]; self.now=0; self.offer_queue={}; self.counter_pending={}
    def register_shipper(self,x): self.shippers[x.id]=x
    def register_carrier(self,x): self.carriers[x.id]=x
    def register_truck(self,x):
        if x.carrier_id not in self.carriers: raise RuleError("Register carrier before truck")
        self.trucks[x.id]=x
    def post_load(self,x):
        if x.shipper_id not in self.shippers: raise RuleError("Register shipper before load")
        validate_load(x); self.loads[x.id]=x
        return price_load(x,list(self.trucks.values()),list(self.loads.values()),self.distances,self.poor_cities)
    def match_cycle(self):
        for load in sorted(self.loads.values(),key=lambda z:z.id):
            if not load.open: continue
            price_load(load,list(self.trucks.values()),list(self.loads.values()),self.distances,self.poor_cities)
            ranked,rejected=eligible_trucks(load,list(self.trucks.values()),self.carriers,self.distances,self.now)
            self.logs.append(f"CYCLE {self.now} LOAD {load.id} PRICE Rs {load.recommended}")
            for tid,why in rejected.items(): self.logs.append(f" REJECT {tid}: {', '.join(why)}")
            if ranked:
                self.offer_queue[load.id]=[t.id for t in ranked[:3]]
                self._offer_next(load.id)
            else: self.logs.append(f" NO ELIGIBLE TRUCKS for {load.id}")
    def _offer_next(self,load_id):
        q=self.offer_queue.get(load_id,[])
        if not q: self.logs.append(f" EXHAUSTED OFFERS for {load_id}"); return
        tid=q.pop(0); load=self.loads[load_id]; truck=self.trucks[tid]
        trip_id=f"TRIP-{load_id}"
        trip=Trip(trip_id,load_id,tid,truck.carrier_id,load.shipper_id,State.MATCHED,self.now,
                  load.recommended,load.price["base_price"],self.now+30)
        self.trips[trip_id]=trip
        self.logs.append(f" OFFER {load_id} -> {tid}; response deadline {self.now+30}")
    def respond_offer(self,load_id,accept,minute=None):
        trip=self.trips[f"TRIP-{load_id}"]; at=self.now if minute is None else minute
        if at > trip.offer_deadline:
            self.logs.append(f" OFFER EXPIRED {load_id}")
            self._offer_next(load_id); return "EXPIRED"
        if accept:
            trip.accepted_at=at; trip.state=State.MATCHED
            self.loads[load_id].open=False
            self.logs.append(f" ACCEPTED {load_id} by {trip.truck_id}")
            return "ACCEPTED"
        self.logs.append(f" DECLINED {load_id} by {trip.truck_id}")
        self._offer_next(load_id); return "DECLINED"
    def advance(self,minutes):
        self.now += int(minutes)
        for lid,trip in list(self.trips.items()):
            if trip.state==State.MATCHED and trip.accepted_at is None and self.now>trip.offer_deadline:
                self.logs.append(f" OFFER TIMEOUT {lid}")
                self._offer_next(trip.load_id)
            pending=self.counter_pending.get(lid)
            if pending and self.now>pending["deadline"]:
                self.logs.append(f" COUNTER LAPSED {lid}"); del self.counter_pending[lid]
    def counter(self,trip_id,amount):
        trip=self.trips[trip_id]
        status=counter_status(trip.agreed_price,amount,0)
        if status=="SHIPPER_DECISION_REQUIRED":
            self.counter_pending[trip_id]={"amount":Decimal(str(amount)),"deadline":self.now+60}
        elif status=="AUTO_ACCEPTED": trip.agreed_price=Decimal(str(amount))
        self.logs.append(f" COUNTER {trip_id} Rs {amount}: {status}")
        return status
    def shipper_counter_decision(self,trip_id,accept):
        p=self.counter_pending.get(trip_id)
        if not p: raise RuleError("No pending shipper counter decision")
        if self.now>p["deadline"]: del self.counter_pending[trip_id]; return "LAPSED"
        if accept: self.trips[trip_id].agreed_price=p["amount"]
        del self.counter_pending[trip_id]
        return "ACCEPTED" if accept else "REJECTED"
    def event(self,trip_id,event,**data):
        t=self.trips[trip_id]; load=self.loads[t.load_id]; truck=self.trucks[t.truck_id]; carrier=self.carriers[t.carrier_id]
        transitions={"AT_PICKUP":(State.MATCHED,State.AT_PICKUP),"LOADED":(State.AT_PICKUP,State.LOADED),
          "IN_TRANSIT":(State.LOADED,State.IN_TRANSIT),"DELIVERED":(State.IN_TRANSIT,State.DELIVERED)}
        if event in transitions:
            old,new=transitions[event]
            if t.state!=old: raise RuleError(f"{event} invalid from {t.state.value}")
            t.state=new
            if event=="DELIVERED":
                update_rating(carrier,"LATE_OVER_4H" if data.get("late_hours",0)>4 else "ON_TIME")
        elif event=="CANCEL_SHIPPER":
            if t.state not in {State.MATCHED}: raise RuleError("Shipper cancellation only before AT_PICKUP")
            t.cancel_fee=cancellation_fee(self.now-t.matched_at,t.base_price); t.state=State.CANCELLED; load.open=True
        elif event=="CANCEL_CARRIER":
            if t.accepted_at is None: raise RuleError("Carrier cancellation requires accepted offer")
            t.cancel_fee=Decimal(2000); update_rating(carrier,"CANCELLED"); t.state=State.CANCELLED; load.open=True
        elif event=="NO_SHOW":
            if t.state!=State.MATCHED or self.now < load.pickup_end: raise RuleError("No-show only at/after pickup window end")
            t.cancel_fee=Decimal(2000); update_rating(carrier,"CANCELLED"); t.state=State.CANCELLED; load.open=True
        elif event=="ABORT":
            if t.state!=State.AT_PICKUP: raise RuleError("Abort only while at pickup")
            charge,_=detention(max(t.pickup_detention,Decimal(54)),truck.truck_type)
            t.settlement={"detention":charge,"abort_base_compensation":rupee(t.base_price*Decimal(".5"))}
            t.state=State.ABORTED
        elif event=="SETTLE":
            if t.state!=State.DELIVERED: raise RuleError("Settlement only after delivery")
            t.pickup_detention=Decimal(str(data.get("pickup_detention_hours",0)))
            t.delivery_detention=Decimal(str(data.get("delivery_detention_hours",0)))
            t.toll_actual=Decimal(str(data.get("toll_actual",0)))
            t.settlement=settle(t,load,truck,carrier,self.shippers[t.shipper_id],self.toll_caps.get((load.origin,load.destination)))
            t.state=State.SETTLED
        else: raise RuleError(f"Unknown event {event}")
        self.logs.append(f" EVENT {trip_id}: {event} -> {t.state.value}")
        return t.state
    def run_demo(self):
        self.match_cycle()
        for load_id in list(self.offer_queue):
            trip=self.trips.get(f"TRIP-{load_id}")
            if trip and trip.accepted_at is None: self.respond_offer(load_id,True)
        for trip_id,t in list(self.trips.items()):
            if t.accepted_at is None: continue
            self.event(trip_id,"AT_PICKUP"); self.event(trip_id,"LOADED"); self.event(trip_id,"IN_TRANSIT")
            self.event(trip_id,"DELIVERED",late_hours=0)
            self.event(trip_id,"SETTLE",toll_actual=500,pickup_detention_hours=7,delivery_detention_hours=6)
    def report(self):
        out=["T069-PS-099 FREIGHT EXCHANGE REPORT","="*42,"PRICE BREAKDOWNS"]
        for l in self.loads.values():
            if l.price: out.append(f"{l.id}: {l.price}")
        out += ["","MATCHING AND EVENT LOG",*self.logs,"","TRIP SETTLEMENTS"]
        for t in self.trips.values():
            out.append(f"{t.id}: {t.state.value}; truck={t.truck_id}; agreed=Rs {t.agreed_price}")
            if t.cancel_fee: out.append(f" cancellation_fee=Rs {rupee(t.cancel_fee)}")
            for k,v in t.settlement.items(): out.append(f" {k}: {v}")
        return "\n".join(out)
