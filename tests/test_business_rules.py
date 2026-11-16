import unittest
from decimal import Decimal
from src.sample_data import build_sample_engine
from src.models import Load, Truck, Carrier, Trip, TripState, Shipper
from src.pricing import PricingEngine
from src.matching import MatchingEngine
from src.bidding import BiddingEngine
from src.settlement import detention_charge
from src.rating import update_rating
from src.validation import RuleViolation, distance_between

class FreightRuleTests(unittest.TestCase):
    def test_br01_minimum_150_km(self):
        p = PricingEngine({("A","B"):149}).calculate(
            Load("L","S","A","B",Decimal("1"),"LCV",0,100,"GENERAL"), [], [])
        self.assertEqual(p["chargeable_km"], Decimal("150"))
        self.assertEqual(p["base_price"], Decimal("2700"))

    def test_br02_unknown_distance_rejected(self):
        with self.assertRaises(RuleViolation):
            distance_between("A","Z",{})

    def test_br03_exact_1_5_no_surge(self):
        # Three open loads / two available trucks = exactly 1.5; threshold is strictly greater.
        distances = {("A","B"):200}
        trucks = [Truck("T1","C","LCV",Decimal(5),Decimal(10),"A",0),
                  Truck("T2","C","LCV",Decimal(5),Decimal(10),"A",0)]
        loads = [Load(f"L{i}","S","A","B",Decimal(1),"LCV",0,10) for i in range(3)]
        p = PricingEngine(distances).calculate(loads[0], trucks, loads)
        self.assertEqual(p["surge_adjustment_pct"], Decimal("0"))

    def test_br04_truck_exactly_150_km_eligible(self):
        carriers = {"C": Carrier("C","Carrier",Decimal("4.0"),second_driver=True)}
        truck = Truck("T","C","LCV",Decimal(5),Decimal(10),"A",0)
        load = Load("L","S","B","C",Decimal(1),"LCV",0,100)
        eligible, _ = MatchingEngine({("A","B"):150,("B","C"):100}, carriers).eligible_trucks(load,[truck])
        self.assertEqual([x.truck_id for x in eligible], ["T"])

    def test_br05_counter_exact_5_percent_auto_accept(self):
        result = BiddingEngine().evaluate_counter(Decimal("10000"), Decimal("10500"), 0)
        self.assertEqual(result, "AUTO_ACCEPTED")

    def test_br06_detention_6h01_is_one_hour(self):
        charge, hours = detention_charge(Decimal("6.0167"), "LCV")
        self.assertEqual(hours, 1)
        self.assertEqual(charge, Decimal("300"))

    def test_br07_shipper_cancel_exact_1_hour_free(self):
        engine = build_sample_engine()
        engine.run_matching_cycle()
        trip = next(iter(engine.trips.values()))
        engine.current_minute = trip.matched_at + 60
        engine.event(trip.trip_id, "CANCEL_SHIPPER")
        self.assertEqual(trip.cancellation_fee, Decimal("0"))

    def test_br08_driver_exact_remaining_buffer(self):
        carriers = {"C": Carrier("C","Carrier",second_driver=False)}
        truck = Truck("T","C","LCV",Decimal(5),Decimal(10),"A",0,Decimal("8.25"))
        load = Load("L","S","B","C",Decimal(1),"LCV",0,100)
        # 150 km = 3.75 h; 3.75 + 2 = 5.75; remaining 5.75 exactly.
        eligible, _ = MatchingEngine({("A","B"):150,("B","C"):100}, carriers).eligible_trucks(load,[truck])
        self.assertEqual(len(eligible), 1)

    def test_br09_rating_floor_and_ceiling(self):
        c = Carrier("C","Carrier",Decimal("1.0"))
        update_rating(c,"CANCELLED")
        self.assertEqual(c.rating, Decimal("1.0"))
        c.rating = Decimal("4.98")
        update_rating(c,"ON_TIME")
        self.assertEqual(c.rating, Decimal("5.0"))

    def test_br10_counter_above_15_rejected(self):
        self.assertEqual(BiddingEngine().evaluate_counter(100,116,0),"REJECTED")

    def test_br11_perishable_window_limit(self):
        engine = build_sample_engine()
        bad = Load("P","SHP-001","Bengaluru","Chennai",Decimal(1),"17FT",0,361,"PERISHABLE")
        with self.assertRaises(RuleViolation):
            engine.post_load(bad)

    def test_br12_hazardous_requires_certification(self):
        carriers={"C":Carrier("C","Carrier",second_driver=True)}
        t=Truck("T","C","LCV",Decimal(5),Decimal(10),"A",0,haz_certified=False)
        l=Load("L","S","B","C",Decimal(1),"LCV",0,100,"HAZARDOUS")
        eligible,_=MatchingEngine({("A","B"):10,("B","C"):20},carriers).eligible_trucks(l,[t])
        self.assertEqual(eligible,[])

    def test_br13_trip_duration_hos_rejection(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=False)}
        truck = Truck("T", "C", "LCV", Decimal(5), Decimal(10), "A", 0, Decimal("11"))
        load = Load("L", "S", "B", "C", Decimal(1), "LCV", 0, 100)
        # Remaining 3 hours; lane estimate is 3.5h and origin ETA plus buffer is 5.75h.
        eligible, _ = MatchingEngine({("A", "B"): 150, ("B", "C"): 100}, carriers).eligible_trucks(load, [truck])
        self.assertEqual(len(eligible), 0)

    def test_br14_carrier_no_show_at_pickup_window_end(self):
        engine = build_sample_engine()
        engine.run_matching_cycle()
        trip = next(iter(engine.trips.values()))
        load = engine.loads[trip.load_id]
        engine.current_minute = load.pickup_end
        engine.event(trip.trip_id, "NO_SHOW")
        self.assertEqual(trip.state, TripState.CANCELLED)
        self.assertEqual(trip.cancellation_fee, Decimal("2000"))

    def test_br15_no_show_before_window_end_rejected(self):
        engine = build_sample_engine()
        engine.run_matching_cycle()
        trip = next(iter(engine.trips.values()))
        with self.assertRaises(RuleViolation):
            engine.event(trip.trip_id, "NO_SHOW")

if __name__ == "__main__":
    unittest.main()
