"""Soil moisture per zone, day by day, with valves that open only where the soil is dry.

All numbers are simulated. Moisture is volumetric water content in percent.
"""
import random
from dataclasses import dataclass, field

DRY_BELOW = 22.0        # open the valve under this
TARGET = 30.0           # water up to this
TOO_DRY = 18.0          # stress level, counted as a bad day
TOO_WET = 36.0          # close to waterlogged; durian roots rot in standing water
FIELD_CAPACITY = 40.0   # soil cannot hold more; the rest runs off
LITRES_PER_POINT = 400  # water a zone needs to rise one moisture point (4 trees, root zone)


@dataclass
class Zone:
    id: str
    moisture: float
    drain: float             # how fast this soil dries, 1.0 = average
    history: list[float] = field(default_factory=list)
    watered: list[bool] = field(default_factory=list)


@dataclass
class Day:
    sun: float               # 0..1, how much evaporation today
    rain_mm: float


def make_weather(days: int, seed: int = 3) -> list[Day]:
    rng = random.Random(seed)
    weather = []
    for d in range(days):
        rain = rng.choice([0, 0, 0, 0, 0, 6, 25]) if d not in (0, 1) else 0
        sun = 0.35 if rain > 10 else rng.uniform(0.7, 1.0)
        weather.append(Day(sun, rain))
    return weather


def make_zones(cols: int, rows: int, seed: int = 3) -> list[Zone]:
    rng = random.Random(seed)
    return [Zone(f"{chr(65 + r)}{c + 1}", rng.uniform(25, 31), rng.uniform(0.75, 1.35))
            for r in range(rows) for c in range(cols)]


def step(zone: Zone, day: Day, smart: bool, scheduled_today: bool) -> float:
    """Advance one day. Returns litres used by this zone today."""
    zone.moisture -= 3.2 * day.sun * zone.drain
    zone.moisture += day.rain_mm * 0.35
    zone.moisture = min(zone.moisture, FIELD_CAPACITY)
    litres = 0.0
    water = (zone.moisture < DRY_BELOW) if smart else scheduled_today
    if water:
        rise = (TARGET - zone.moisture) if smart else 6.0
        if rise > 0:
            zone.moisture = min(zone.moisture + rise, FIELD_CAPACITY)  # water past capacity is wasted
            litres = rise * LITRES_PER_POINT
    zone.history.append(zone.moisture)
    zone.watered.append(bool(water and litres))
    return litres


def run(days: int, smart: bool, cols: int = 4, rows: int = 3, every: int = 2) -> tuple[list[Zone], list[Day], float]:
    zones, weather = make_zones(cols, rows), make_weather(days)
    total = 0.0
    for d, day in enumerate(weather):
        for z in zones:
            total += step(z, day, smart, scheduled_today=(d % every == 0))
    return zones, weather, total


def dry_days(zones: list[Zone]) -> int:
    return sum(1 for z in zones for m in z.history if m < TOO_DRY)


def wet_days(zones: list[Zone]) -> int:
    return sum(1 for z in zones for m in z.history if m > TOO_WET)
