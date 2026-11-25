import unittest
from decimal import Decimal as D

from app.models import Carrier, Load, Truck
from app.services import eligible_trucks


class MatchingAndHosTests(unittest.TestCase):
    def test_truck_exact_150_km_is_eligible(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=True)}
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        load = Load("L", "S", "B", "C", D(1), "LCV", 0, 100)
        ok, _ = eligible_trucks(load, [truck], carriers, {("A", "B"): 150, ("B", "C"): 100})
        self.assertEqual([x.id for x in ok], ["T"])

    def test_truck_over_150_km_rejected(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=True)}
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        load = Load("L", "S", "B", "C", D(1), "LCV", 0, 100)
        ok, rej = eligible_trucks(load, [truck], carriers, {("A", "B"): 151, ("B", "C"): 100})
        self.assertFalse(ok)
        self.assertIn("more than 150 km from origin", rej["T"])

    def test_one_size_larger_truck_allowed(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=True)}
        t_ok = Truck("T1", "C", "17FT", D(8), D(17), "A")
        t_too_big = Truck("T2", "C", "22FT", D(14), D(22), "A")
        load = Load("L", "S", "A", "B", D(2), "LCV", 0, 100)
        ok, rej = eligible_trucks(load, [t_ok, t_too_big], carriers, {("A", "B"): 100})
        self.assertEqual([t.id for t in ok], ["T1"])
        self.assertIn("truck type", rej["T2"])

    def test_hos_exact_buffer_allowed(self):
        carriers = {"C": Carrier("C", "Carrier")}
        # 150 / 40 + 2 = 5.75h; 14 - 8.25 = 5.75h exact
        truck = Truck("T", "C", "LCV", D(5), D(10), "A", hours_used=D("8.25"))
        load = Load("L", "S", "B", "C", D(1), "LCV", 0, 100)
        ok, _ = eligible_trucks(load, [truck], carriers, {("A", "B"): 150, ("B", "C"): 100})
        self.assertEqual(len(ok), 1)

    def test_second_driver_waives_hos_rejection(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=True)}
        truck = Truck("T", "C", "LCV", D(5), D(10), "A", hours_used=D(13))
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100)
        ok, _ = eligible_trucks(load, [truck], carriers, {("A", "B"): 500})
        self.assertEqual(len(ok), 1)

    def test_haz_cert_required(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=True)}
        truck = Truck("T", "C", "LCV", D(5), D(10), "A", haz_certified=False)
        load = Load("L", "S", "B", "C", D(1), "LCV", 0, 100, "HAZARDOUS")
        ok, rej = eligible_trucks(load, [truck], carriers, {("A", "B"): 10, ("B", "C"): 20})
        self.assertFalse(ok)
        self.assertIn("HAZ certification", rej["T"])

    def test_oversize_length_rejected(self):
        carriers = {"C": Carrier("C", "Carrier", second_driver=True)}
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        load = Load("L", "S", "B", "C", D(1), "LCV", 0, 100, "OVERSIZE", D(12))
        ok, rej = eligible_trucks(load, [truck], carriers, {("A", "B"): 10, ("B", "C"): 20})
        self.assertFalse(ok)
        self.assertIn("oversize length", rej["T"])

    def test_rating_below_3_excluded_and_ranking_tie_break(self):
        carriers = {
            "C_LOW": Carrier("C_LOW", "Low", D("2.9"), second_driver=True),
            "C_A": Carrier("C_A", "A", D("4.5"), second_driver=True),
            "C_B": Carrier("C_B", "B", D("4.8"), second_driver=True),
        }
        trucks = [
            Truck("T_LOW", "C_LOW", "LCV", D(5), D(10), "A"),
            Truck("T2", "C_A", "LCV", D(5), D(10), "A"),
            Truck("T1", "C_B", "LCV", D(5), D(10), "A"),
        ]
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100)
        ok, rej = eligible_trucks(load, trucks, carriers, {("A", "B"): 100})
        self.assertEqual([t.id for t in ok], ["T1", "T2"])
        self.assertIn("rating below 3.0", rej["T_LOW"])


if __name__ == "__main__":
    unittest.main()
