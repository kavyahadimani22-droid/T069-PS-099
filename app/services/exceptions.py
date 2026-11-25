"""Shared exceptions and decimal/lane utility helpers."""

from decimal import Decimal, ROUND_HALF_UP


class RuleError(ValueError):
    """Raised when a freight exchange business rule or state transition is violated."""


def D(value) -> Decimal:
    """Convert numeric or string values safely into Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def rupee(value) -> Decimal:
    """Round monetary amount to nearest whole rupee using half-up rounding."""
    return D(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def lane_km(distances: dict[tuple[str, str], int | float | Decimal], origin: str, destination: str) -> Decimal:
    """Look up symmetric city-to-city lane distance in km; raise RuleError if unknown."""
    if origin == destination:
        return Decimal("0")
    if (origin, destination) in distances:
        return D(distances[(origin, destination)])
    if (destination, origin) in distances:
        return D(distances[(destination, origin)])
    raise RuleError(f"Unknown city pair: {origin} -> {destination}")
