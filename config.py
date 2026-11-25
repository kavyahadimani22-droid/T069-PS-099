from decimal import Decimal
RATES = {"LCV": Decimal("18"), "17FT": Decimal("24"), "22FT": Decimal("32"), "32FT_MXL": Decimal("45"), "TRAILER": Decimal("60")}
DETENTION_RATES = {"LCV": Decimal("300"), "17FT": Decimal("500"), "22FT": Decimal("500"), "32FT_MXL": Decimal("800"), "TRAILER": Decimal("800")}
TYPE_ORDER = ["LCV", "17FT", "22FT", "32FT_MXL", "TRAILER"]
MIN_KM = Decimal("150")
