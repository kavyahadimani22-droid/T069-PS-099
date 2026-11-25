import unittest
from decimal import Decimal as D
from src.rules import *
from src.models import *
from src.engine import FreightEngine

class RuleTests(unittest.TestCase):
    def test_min_149(self):
        l=Load("L","S","A","B",D(1),"LCV",0,100)
        p=price_load(l,[],[l],{("A","B"):149},set())
        self.assertEqual(p["chargeable_km"],D(150)); self.assertEqual(p["base_price"],D(2700))
    def test_unknown_lane(self):
        with self.assertRaises(RuleError): lane_km({}, "A","B")
    def test_ratio_exact_15(self):
        ts=[Truck("T1","C","LCV",D(5),D(10),"A"),Truck("T2","C","LCV",D(5),D(10),"A")]
        ls=[Load(f"L{i}","S","A","B",D(1),"LCV",0,10) for i in range(3)]
        p=price_load(ls[0],ts,ls,{("A","B"):200},set())
        self.assertEqual(p["surge_pct"],D(0))
    def test_truck_exact_150(self):
        c={"C":Carrier("C","Carrier",second_driver=True)}
        t=Truck("T","C","LCV",D(5),D(10),"A")
        l=Load("L","S","B","C",D(1),"LCV",0,100)
        ok,_=eligible_trucks(l,[t],c,{("A","B"):150,("B","C"):100})
        self.assertEqual([x.id for x in ok],["T"])
    def test_counter_exact_5(self): self.assertEqual(counter_status(100,105,0),"AUTO_ACCEPTED")
    def test_counter_exact_15(self): self.assertEqual(counter_status(100,115,60),"SHIPPER_DECISION_REQUIRED")
    def test_counter_over_15(self): self.assertEqual(counter_status(100,115.01,0),"REJECTED")
    def test_detention_6h1m(self): self.assertEqual(detention(D("6.0166667"),"LCV"),(D(300),1))
    def test_cancel_exact_1h(self): self.assertEqual(cancellation_fee(60,10000),D(0))
    def test_cancel_6h(self): self.assertEqual(cancellation_fee(360,10000),D(1000))
    def test_hos_exact_buffer(self):
        c={"C":Carrier("C","Carrier")}
        t=Truck("T","C","LCV",D(5),D(10),"A",hours_used=D("8.25"))
        l=Load("L","S","B","C",D(1),"LCV",0,100)
        ok,_=eligible_trucks(l,[t],c,{("A","B"):150,("B","C"):100})
        self.assertEqual(len(ok),1)
    def test_haz_cert(self):
        c={"C":Carrier("C","Carrier",second_driver=True)}
        t=Truck("T","C","LCV",D(5),D(10),"A",haz_certified=False)
        l=Load("L","S","B","C",D(1),"LCV",0,100,"HAZARDOUS")
        ok,_=eligible_trucks(l,[t],c,{("A","B"):10,("B","C"):20})
        self.assertFalse(ok)
    def test_perishable_over_6h(self):
        l=Load("L","S","A","B",D(1),"LCV",0,361,"PERISHABLE")
        with self.assertRaises(RuleError): validate_load(l)
    def test_oversize(self):
        c={"C":Carrier("C","Carrier",second_driver=True)}
        t=Truck("T","C","LCV",D(5),D(10),"A")
        l=Load("L","S","B","C",D(1),"LCV",0,100,"OVERSIZE",D(12))
        ok,_=eligible_trucks(l,[t],c,{("A","B"):10,("B","C"):20})
        self.assertFalse(ok)
    def test_rating_cutoff(self):
        c={"C":Carrier("C","Carrier",D("2.9"),second_driver=True)}
        t=Truck("T","C","LCV",D(5),D(10),"A")
        l=Load("L","S","B","C",D(1),"LCV",0,100)
        ok,_=eligible_trucks(l,[t],c,{("A","B"):10,("B","C"):20})
        self.assertFalse(ok)
    def test_rating_bound(self):
        c=Carrier("C","Carrier",D("4.98")); update_rating(c,"ON_TIME"); self.assertEqual(c.rating,D(5))
    def test_toll_cap_and_settlement(self):
        c=Carrier("C","Carrier"); s=Shipper("S","Ship",True)
        l=Load("L","S","A","B",D(1),"LCV",0,100)
        t=Truck("T","C","LCV",D(5),D(10),"A")
        trip=Trip("TR","L","T","C","S",State.DELIVERED,0,D(10000),D(10000),30)
        trip.toll_actual=D(500)
        result=settle(trip,l,t,c,s,300)
        self.assertEqual(result["toll"],D(330))
        self.assertTrue(result["rcm_flag"])
    def test_cumulative_tds_crossing(self):
        c=Carrier("C","Carrier",annual_payout=D(99900))
        s=Shipper("S","Ship"); l=Load("L","S","A","B",D(1),"LCV",0,100)
        t=Truck("T","C","LCV",D(5),D(10),"A")
        trip=Trip("TR","L","T","C","S",State.DELIVERED,0,D(5000),D(5000),30)
        result=settle(trip,l,t,c,s)
        self.assertGreater(result["tds"],D(0))
    def test_matching_timeout_next_truck(self):
        e=FreightEngine({("A","B"):100})
        e.register_shipper(Shipper("S","Shipper"))
        e.register_carrier(Carrier("C1","one",second_driver=True))
        e.register_carrier(Carrier("C2","two",second_driver=True))
        e.register_truck(Truck("T1","C1","LCV",D(5),D(10),"A"))
        e.register_truck(Truck("T2","C2","LCV",D(5),D(10),"A"))
        e.post_load(Load("L","S","A","B",D(1),"LCV",0,100))
        e.match_cycle(); self.assertEqual(e.trips["TRIP-L"].truck_id,"T1")
        e.advance(31); self.assertEqual(e.trips["TRIP-L"].truck_id,"T2")

    def test_surge_over_4(self):
        ts=[Truck("T0","C","LCV",D(5),D(10),"A")]
        ls=[Load(f"L{i}","S","A","B",D(1),"LCV",0,10) for i in range(5)]
        p=price_load(ls[0],ts,ls,{("A","B"):200},set())
        self.assertEqual(p["surge_pct"],D("30.00"))
    def test_return_load_discount_three(self):
        target=Load("TARGET","S","A","B",D(1),"LCV",0,10)
        backs=[Load(f"R{i}","S","B","A",D(1),"LCV",0,10) for i in range(3)]
        p=price_load(target,[],[target]+backs,{("A","B"):200},set())
        self.assertEqual(p["return_load_pct"],D("-8.00"))
    def test_detention_48_hour_cap(self):
        charge,hours=detention(100,"LCV")
        self.assertEqual(hours,48); self.assertEqual(charge,D(14400))
    def test_second_driver_allows_hos(self):
        c={"C":Carrier("C","Carrier",second_driver=True)}
        t=Truck("T","C","LCV",D(5),D(10),"A",hours_used=D(13))
        l=Load("L","S","A","B",D(1),"LCV",0,100)
        ok,_=eligible_trucks(l,[t],c,{("A","B"):500})
        self.assertEqual(len(ok),1)
    def test_counter_shipper_window(self):
        e=FreightEngine({("A","B"):100})
        e.register_shipper(Shipper("S","Ship")); e.register_carrier(Carrier("C","C",second_driver=True))
        e.register_truck(Truck("T","C","LCV",D(5),D(10),"A"))
        e.post_load(Load("L","S","A","B",D(1),"LCV",0,100)); e.match_cycle(); e.respond_offer("L",True)
        recommended=e.trips["TRIP-L"].agreed_price
        counter=rupee(recommended*D("1.10"))
        self.assertEqual(e.counter("TRIP-L",counter),"SHIPPER_DECISION_REQUIRED")
        self.assertEqual(e.shipper_counter_decision("TRIP-L",True),"ACCEPTED")
        self.assertEqual(e.trips["TRIP-L"].agreed_price,counter)

if __name__=="__main__": unittest.main()
