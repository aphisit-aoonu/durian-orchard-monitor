from durian.irrigation import DRY_BELOW, FIELD_CAPACITY, TARGET, Day, Zone, dry_days, run, step, wet_days


def test_valve_opens_only_when_dry_and_fills_to_target():
    z = Zone("A1", moisture=DRY_BELOW + 0.5, drain=1.0)
    used = step(z, Day(sun=1.0, rain_mm=0), smart=True, scheduled_today=False)
    assert used > 0
    assert z.moisture == TARGET


def test_wet_zone_is_left_alone():
    z = Zone("A1", moisture=35, drain=1.0)
    assert step(z, Day(sun=1.0, rain_mm=0), smart=True, scheduled_today=False) == 0


def test_rain_raises_moisture():
    z = Zone("A1", moisture=25, drain=1.0)
    step(z, Day(sun=0.0, rain_mm=20), smart=True, scheduled_today=False)
    assert z.moisture > 25


def test_smart_watering_uses_less_water_and_never_lets_soil_get_too_dry():
    smart_zones, _, smart_litres = run(14, smart=True)
    fixed_zones, _, fixed_litres = run(14, smart=False)
    assert smart_litres < fixed_litres
    assert dry_days(smart_zones) == 0


def test_moisture_never_exceeds_field_capacity():
    zones, _, _ = run(14, smart=False)
    assert max(m for z in zones for m in z.history) <= FIELD_CAPACITY


def test_smart_watering_keeps_soil_from_getting_waterlogged():
    smart_zones, _, _ = run(14, smart=True)
    fixed_zones, _, _ = run(14, smart=False)
    assert wet_days(smart_zones) < wet_days(fixed_zones)
