from datetime import datetime,timedelta
from decimal import Decimal as D
import pytest
from src.models import Carrier,Load,Truck,Trip,State
from src.file_handler import Market
from src.pricing import calculate_price,surge_rate
from src.matching import eligible,rank_trucks
from src.bidding import evaluate_counteroffer,offer_expired,counter_expired
from src.settlement import detention_charge,cancellation_charge,toll_charge,tds_amount
from src.ratings import update_rating,is_rankable
from src.trip_management import transition
NOW=datetime(2026,11,6,8)
@pytest.fixture
def market():
    m=Market();m.carriers["C1"]=Carrier("C1")
    m.distances.update({("A","B"):D(149),("B","A"):D(149)})
    return m
def mkload(**kw):
    d=dict(load_id="L",shipper_id="S",origin="A",destination="B",weight_tonnes=D(5),truck_type="LCV",pickup_start=NOW,pickup_end=NOW+timedelta(hours=6),material_class="GENERAL",length_ft=D(10),open=True);d.update(kw);return Load(**d)
def mktruck(**kw):
    d=dict(truck_id="T",carrier_id="C1",truck_type="LCV",capacity_tonnes=D(10),length_ft=D(20),current_city="A",available_from=NOW,driver_hours_used=D(0),haz_certified=False,second_driver=False,active=True);d.update(kw);return Truck(**d)
def test_BR01_BR02_rates_and_minimum(market):
    for kind,rate in [("LCV",18),("17FT",24),("22FT",32),("32FT_MXL",45),("TRAILER",60)]:
        p=calculate_price(market,mkload(truck_type=kind),[],[])
        assert p.chargeable_km==150 and p.base==D(150*rate)
@pytest.mark.parametrize("r,e",[("1.5",0),("1.5001",".1"),("2.5",".1"),("2.5001",".2"),("4",".2"),("4.0001",".3"),(".5",0),(".4999","-.1")])
def test_BR03_surge_edges(r,e):assert surge_rate(D(r))==D(str(e))
def test_BR04_BR05_backhaul_and_poor_city(market):
    l=mkload();market.loads["L"]=l
    for i in range(3):market.loads[str(i)]=mkload(load_id=str(i),origin="B",destination="A")
    market.backhaul_poor.add("B");p=calculate_price(market,l,[],[])
    assert p.return_pct==D(".08") and p.poor_pct==D(".12")
def test_BR06_material_rules(market):
    assert calculate_price(market,mkload(material_class="HAZARDOUS"),[],[]).material_pct==D(".15")
    assert calculate_price(market,mkload(material_class="PERISHABLE"),[],[]).material_pct==D(".10")
    with pytest.raises(ValueError):calculate_price(market,mkload(material_class="PERISHABLE",pickup_end=NOW+timedelta(hours=7)),[],[])
def test_BR07_exact_150km_and_oversize(market):
    market.distances["X","A"]=D(150);t=mktruck(current_city="X")
    assert eligible(market,mkload(),t)[0]
    assert not eligible(market,mkload(length_ft=D(21)),t)[0]
def test_BR08_exact_hours_buffer_and_second_driver(market):
    # 0km approach estimates 1h; plus 2h buffer => exactly 3h remaining.
    assert eligible(market,mkload(),mktruck(driver_hours_used=D(11)))[0]
    assert not eligible(market,mkload(),mktruck(driver_hours_used=D("11.01")))[0]
    assert eligible(market,mkload(),mktruck(driver_hours_used=D(14),second_driver=True))[0]
def test_BR09_ranking(market):
    market.distances.update({("X","A"):D(2),("Y","A"):D(2)})
    market.carriers["C2"]=Carrier("C2",rating=D("4.5"))
    a=mktruck(truck_id="T2",current_city="X");b=mktruck(truck_id="T1",carrier_id="C2",current_city="Y")
    market.trucks={"T2":a,"T1":b}
    assert [t.truck_id for t in rank_trucks(market,mkload())]==["T1","T2"]
def test_BR10_BR12_deadlines():
    assert not offer_expired(NOW,NOW+timedelta(minutes=30))
    assert offer_expired(NOW,NOW+timedelta(minutes=30,seconds=1))
    assert not counter_expired(NOW,NOW+timedelta(minutes=60))
    assert counter_expired(NOW,NOW+timedelta(minutes=60,seconds=1))
def test_BR11_counter_boundaries():
    assert evaluate_counteroffer(100,105)=="AUTO_ACCEPTED"
    assert evaluate_counteroffer(100,115)=="SHIPPER_RESPONSE_REQUIRED"
    assert evaluate_counteroffer(100,115.01)=="REJECTED"
def test_BR13_trip_state_machine():
    t=Trip("TR","L","T","C1","S",D(100),NOW)
    for st in [State.AT_PICKUP,State.LOADED,State.IN_TRANSIT,State.DELIVERED,State.SETTLED]:transition(t,st)
    with pytest.raises(ValueError):transition(t,State.CANCELLED)
def test_BR14_detention_edges():
    assert detention_charge("LCV",D("6.01"),6)==300
    assert detention_charge("LCV",60,60)==14400
def test_BR15_cancellation_edges():
    assert cancellation_charge("shipper",1,10000)==0
    assert cancellation_charge("shipper",6,10000)==1000
    assert cancellation_charge("shipper",D("6.01"),10000)==1000
    assert cancellation_charge("carrier",0,10000)==2000
def test_BR16_toll_cap():assert toll_charge(200,100)==110
def test_BR17_settlement_fields():
    from src.settlement import settle
    x=settle(10000,"LCV",100,100,shipper_registered=True)
    assert x["platform_fee"]==600 and x["rcm_flag"] is True and x["gst"]==500
def test_BR18_tds_and_ratings():
    assert tds_amount(31000,0)==310 and tds_amount(2000,99000)==20 and tds_amount(2000,97000)==0
    c=Carrier("C",rating=D("4.98"));assert update_rating(c,"ON_TIME")==5
    c.rating=D("3");update_rating(c,"CANCELLATION");assert not is_rankable(c)
