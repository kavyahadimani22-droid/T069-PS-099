import unittest
from decimal import Decimal as D

from app.models import Carrier, Load, Shipper, Truck
from app.services import FreightEngine, counter_status, rupee


class BiddingAndTimeoutTests(unittest.TestCase):
    def test_counter_thresholds(self):
        self.assertEqual(counter_status(100, 105, 0), "AUTO_ACCEPTED")
        self.assertEqual(counter_status(100, 115, 60), "SHIPPER_DECISION_REQUIRED")
        self.assertEqual(counter_status(100, 115, 61), "LAPSED")
        self.assertEqual(counter_status(100, 115.01, 0), "REJECTED")

    def test_offer_timeout_moves_to_next_ranked_truck(self):
        engine = FreightEngine({("A", "B"): 100})
        engine.register_shipper(Shipper("S", "Shipper"))
        engine.register_carrier(Carrier("C1", "One", second_driver=True))
        engine.register_carrier(Carrier("C2", "Two", second_driver=True))
        engine.register_truck(Truck("T1", "C1", "LCV", D(5), D(10), "A"))
        engine.register_truck(Truck("T2", "C2", "LCV", D(5), D(10), "A"))
        engine.post_load(Load("L", "S", "A", "B", D(1), "LCV", 0, 100))

        engine.match_cycle()
        self.assertEqual(engine.trips["TRIP-L"].truck_id, "T1")
        engine.advance(31)
        self.assertEqual(engine.trips["TRIP-L"].truck_id, "T2")

    def test_counter_shipper_window_accept(self):
        engine = FreightEngine({("A", "B"): 100})
        engine.register_shipper(Shipper("S", "Ship"))
        engine.register_carrier(Carrier("C", "C", second_driver=True))
        engine.register_truck(Truck("T", "C", "LCV", D(5), D(10), "A"))
        engine.post_load(Load("L", "S", "A", "B", D(1), "LCV", 0, 100))
        engine.match_cycle()
        engine.respond_offer("L", True)

        recommended = engine.trips["TRIP-L"].agreed_price
        counter = rupee(recommended * D("1.10"))
        self.assertEqual(engine.counter("TRIP-L", counter), "SHIPPER_DECISION_REQUIRED")
        self.assertEqual(engine.shipper_counter_decision("TRIP-L", True), "ACCEPTED")
        self.assertEqual(engine.trips["TRIP-L"].agreed_price, counter)


if __name__ == "__main__":
    unittest.main()
