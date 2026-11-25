import unittest
from decimal import Decimal as D

from app.models import Load, Truck
from app.services import RuleError, lane_km, price_load, validate_load


class PricingRuleTests(unittest.TestCase):
    def test_min_chargeable_distance_149_to_150(self):
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100)
        price = price_load(load, [], [load], {("A", "B"): 149}, set())
        self.assertEqual(price["chargeable_km"], D(150))
        self.assertEqual(price["base_price"], D(2700))

    def test_unknown_lane_raises_rule_error(self):
        with self.assertRaises(RuleError):
            lane_km({}, "A", "B")

    def test_exact_15_ratio_has_no_surge(self):
        trucks = [Truck("T1", "C", "LCV", D(5), D(10), "A"), Truck("T2", "C", "LCV", D(5), D(10), "A")]
        loads = [Load(f"L{i}", "S", "A", "B", D(1), "LCV", 0, 10) for i in range(3)]
        price = price_load(loads[0], trucks, loads, {("A", "B"): 200}, set())
        self.assertEqual(price["surge_pct"], D(0))

    def test_surge_over_4_adds_30_pct(self):
        trucks = [Truck("T0", "C", "LCV", D(5), D(10), "A")]
        loads = [Load(f"L{i}", "S", "A", "B", D(1), "LCV", 0, 10) for i in range(5)]
        price = price_load(loads[0], trucks, loads, {("A", "B"): 200}, set())
        self.assertEqual(price["surge_pct"], D("30.00"))

    def test_low_demand_below_half_deducts_10_pct(self):
        trucks = [Truck(f"T{i}", "C", "LCV", D(5), D(10), "A") for i in range(3)]
        load = Load("L0", "S", "A", "B", D(1), "LCV", 0, 10)
        price = price_load(load, trucks, [load], {("A", "B"): 200}, set())
        self.assertEqual(price["surge_pct"], D("-10.00"))

    def test_return_load_discount_with_three_qualifying_loads(self):
        target = Load("TARGET", "S", "A", "B", D(1), "LCV", 0, 10)
        backs = [Load(f"R{i}", "S", "B", "A", D(1), "LCV", 0, 10) for i in range(3)]
        price = price_load(target, [], [target] + backs, {("A", "B"): 200}, set())
        self.assertEqual(price["return_load_pct"], D("-8.00"))

    def test_backhaul_poor_and_hazardous_additive(self):
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        load = Load("L", "S", "A", "Delhi", D(1), "LCV", 0, 100, material="HAZARDOUS")
        price = price_load(load, [truck], [load], {("A", "Delhi"): 200}, {"Delhi"})
        self.assertEqual(price["backhaul_poor_pct"], D("12.00"))
        self.assertEqual(price["material_pct"], D("15.00"))
        self.assertEqual(price["recommended_price"], D(4572))

    def test_perishable_over_6h_rejected(self):
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 361, "PERISHABLE")
        with self.assertRaises(RuleError):
            validate_load(load)

    def test_optional_multidrop_and_fuel_index(self):
        truck = Truck("T", "C", "LCV", D(5), D(10), "A")
        load = Load("L", "S", "A", "B", D(1), "LCV", 0, 100, extra_stops=2)
        price = price_load(load, [truck], [load], {("A", "B"): 200}, set(), fuel_index_pct=D(5), extra_stop_fee=D(500))
        # base 3600 * 1.05 + 1000 = 4780
        self.assertEqual(price["recommended_price"], D(4780))


if __name__ == "__main__":
    unittest.main()
