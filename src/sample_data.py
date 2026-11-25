from decimal import Decimal
from src.engine import FreightEngine
from src.models import Shipper,Carrier,Truck,Load

def create_engine():
    distances={("Bengaluru","Chennai"):350,("Bengaluru","Hyderabad"):570,
      ("Bengaluru","Mumbai"):980,("Bengaluru","Pune"):840,("Bengaluru","Mysuru"):145,
      ("Bengaluru","Coimbatore"):360,("Chennai","Hyderabad"):625,("Chennai","Coimbatore"):500,
      ("Hyderabad","Mumbai"):710,("Mumbai","Pune"):150,("Delhi","Mumbai"):1420,
      ("Delhi","Hyderabad"):1550,("Mysuru","Coimbatore"):200,("Pune","Hyderabad"):560}
    e=FreightEngine(distances,{"Delhi","Coimbatore"},
      {("Bengaluru","Chennai"):700,("Chennai","Bengaluru"):700})
    e.register_shipper(Shipper("SHP-001","Acme Manufacturing",True))
    e.register_shipper(Shipper("SHP-002","Fresh Foods Ltd",False))
    e.register_carrier(Carrier("CAR-001","SouthLine Logistics",Decimal("4.6"),second_driver=True))
    e.register_carrier(Carrier("CAR-002","Rapid Freight",Decimal("4.2")))
    e.register_carrier(Carrier("CAR-003","Budget Carriers",Decimal("3.7")))
    e.register_carrier(Carrier("CAR-004","Low Rated Transport",Decimal("2.8")))
    e.register_truck(Truck("TRK-001","CAR-001","17FT",Decimal(8),Decimal(17),"Bengaluru",0,Decimal(5),True))
    e.register_truck(Truck("TRK-002","CAR-002","22FT",Decimal(14),Decimal(22),"Mysuru",0,Decimal(8)))
    e.register_truck(Truck("TRK-003","CAR-003","17FT",Decimal(7),Decimal(17),"Chennai",0,Decimal(3)))
    e.register_truck(Truck("TRK-004","CAR-004","17FT",Decimal(10),Decimal(17),"Bengaluru",0,Decimal(2)))
    e.register_truck(Truck("TRK-005","CAR-001","32FT_MXL",Decimal(25),Decimal(32),"Hyderabad",0,Decimal(4),True))
    e.register_truck(Truck("TRK-006","CAR-002","LCV",Decimal(3),Decimal(10),"Bengaluru",0,Decimal(4)))
    e.post_load(Load("LD-001","SHP-001","Bengaluru","Chennai",Decimal(6),"17FT",60,480,"GENERAL",Decimal(14)))
    return e
