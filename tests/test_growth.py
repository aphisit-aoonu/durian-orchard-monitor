from datetime import date

from durian.growth import TreeState, due_in_week


def test_status_against_six_metre_reach():
    assert TreeState("a", 4.8, 0.7).status() == "ok"
    assert TreeState("b", 5.7, 0.7).status() == "soon"
    assert TreeState("c", 6.3, 0.7).status() == "over"


def test_days_until_over():
    assert TreeState("a", 5.0, 1.0).days_until_over() == 366
    assert TreeState("b", 6.2, 1.0).days_until_over() == 0
    assert TreeState("c", 5.0, 0.0).days_until_over() is None


def test_height_after_a_year():
    assert TreeState("a", 5.0, 0.8).height_after(365) == 5.8


def test_harvest_is_120_days_after_bloom():
    t = TreeState("a", 5.0, 0.7, bloom=date(2026, 1, 10))
    assert t.harvest_date() == date(2026, 5, 10)
    assert t.days_to_harvest(date(2026, 5, 4)) == 6
    assert t.days_to_harvest(date(2026, 5, 12)) == -2
    assert TreeState("b", 5.0, 0.7).days_to_harvest(date(2026, 5, 4)) is None


def test_due_in_week_keeps_only_that_week_in_date_order():
    trees = [TreeState("late", 5, 0.7, date(2026, 1, 9)), TreeState("early", 5, 0.7, date(2026, 1, 5)),
             TreeState("next", 5, 0.7, date(2026, 1, 12)), TreeState("none", 5, 0.7)]
    assert [t.id for t in due_in_week(trees, date(2026, 5, 4))] == ["early", "late"]
    assert [t.id for t in due_in_week(trees, date(2026, 5, 11))] == ["next"]
