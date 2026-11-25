import unittest
from decimal import Decimal as D

from app.models import Carrier, Load, Shipper, State, Truck
from app.services import FreightEngine, RuleError, cancellation_fee, detention, update_rating


class TripLifecycleAndCancellationTests(unittest.TestCase):
    def test_detention_6h1m_and_48h_cap(self):
        self.assertEqual(detention(D("6.0166667"), "LCV"), (D(300), 1))
        charge, hours = detention(100, "LCV")
        self.assertEqual(hours, 48)
        self.assertEqual(charge, D(14400))

    def test_shipper_cancellation_tiers(self):
        self.assertEqual(cancellation_fee(60, 10000), D(0))
        self.assertEqual(cancellation_fee(360, 10000), D(1000))
        self.assertEqual(cancellation_fee(361, 10000), D(1000))
        self.assertEqual(cancellation_fee(400, 25000), D(2500))

    def test_rating_bounds(self):
        carrier = Carrier("C", "Carrier", D("4.98"))
        update_rating(carrier, "ON_TIME")
        self.assertEqual(carrier.rating, D(5))
        carrier_low = Carrier("C2", "Low", D("1.05"))
        update_rating(carrier_low, "CANCELLED")
        self.assertEqual(carrier_low.rating, D(1))

    def test_no_show_and_abort_workflows(self):
        engine = FreightEngine({("A", "B"): 200})
        engine.register_shipper(Shipper("S", "Shipper"))
        engine.register_carrier(Carrier("C", "Carrier", D("4.0"), second_driver=True))
        engine.register_truck(Truck("T", "C", "17FT", D(8), D(17), "A"))
        engine.post_load(Load("L1", "S", "A", "B", D(5), "17FT", 0, 100))
        engine.post_load(Load("L2", "S", "A", "B", D(5), "17FT", 0, 100))
        engine.match_cycle()
        engine.respond_offer("L1", True)
        engine.respond_offer("L2", True)

        with self.assertRaises(RuleError):
            engine.event("TRIP-L1", "NO_SHOW")

        engine.advance(100)
        self.assertEqual(engine.event("TRIP-L1", "NO_SHOW"), State.CANCELLED)
        self.assertEqual(engine.trips["TRIP-L1"].cancel_fee, D(2000))
        self.assertEqual(engine.carriers["C"].rating, D("3.8"))

        engine.event("TRIP-L2", "AT_PICKUP")
        self.assertEqual(engine.event("TRIP-L2", "ABORT", pickup_detention_hours=54), State.ABORTED)
        self.assertEqual(engine.trips["TRIP-L2"].settlement["detention"], D(24000))


if __name__ == "__main__":
    unittest.main()
