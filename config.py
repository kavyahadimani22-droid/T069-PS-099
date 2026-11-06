from decimal import Decimal
RATES = {"LCV": Decimal("18"), "17FT": Decimal("24"), "22FT": Decimal("32"),
         "32FT_MXL": Decimal("45"), "TRAILER": Decimal("60")}
TYPES = ["LCV", "17FT", "22FT", "32FT_MXL", "TRAILER"]
MIN_KM = Decimal("150")
