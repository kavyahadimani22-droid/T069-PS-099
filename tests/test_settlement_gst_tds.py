import unittest
from decimal import Decimal as D

from app.models import Carrier, Load, Shipper, State, Trip, Truck
from app.services import settle


class SettlementGstTdsTests(unittest.TestCase):
    def test_toll_cap_and_rcm_settlement(self):
        carrier = Carrier("C", "Carrier")
        shipper = Shipper("S", "Ship", True)
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100)
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        trip = Trip("TR", "L", "T", "C", "S", State.DELIVERED, 0, D(10000), D(10000), 30)
        trip.toll_actual = D(500)

        result = settle(trip, load, truck, carrier, shipper, 300)
        self.assertEqual(result["toll"], D(330))
        self.assertEqual(result["platform_fee"], D(600))
        self.assertEqual(result["gst"], D(500))
        self.assertTrue(result["rcm_flag"])

    def test_cumulative_tds_crossing_100k(self):
        carrier = Carrier("C", "Carrier", annual_payout=D(99900))
        shipper = Shipper("S", "Ship", False)
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100)
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        trip = Trip("TR", "L", "T", "C", "S", State.DELIVERED, 0, D(5000), D(5000), 30)

        result = settle(trip, load, truck, carrier, shipper)
        self.assertGreater(result["tds"], D(0))
        self.assertFalse(result["rcm_flag"])

    def test_tds_not_charged_at_exact_30000_before_tds(self):
        carrier = Carrier("C", "Carrier", annual_payout=D(0))
        shipper = Shipper("S", "Ship", False)
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100)
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        # base=30000 -> platform=1800 -> before_tds = 31800 - 1800 = 30000 exact
        trip = Trip("TR", "L", "T", "C", "S", State.DELIVERED, 0, D(31800), D(30000), 30)

        result = settle(trip, load, truck, carrier, shipper)
        self.assertEqual(result["tds"], D(0))


if __name__ == "__main__":
    unittest.main()
