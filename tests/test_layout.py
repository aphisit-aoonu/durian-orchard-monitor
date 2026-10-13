import math

from durian.layout import Orchard


def _rail_points(o, step=0.25):
    return [o.point_at(k * step) for k in range(int(o.rail_length / step))]


def test_rail_never_runs_through_a_canopy():
    o = Orchard()
    pts = _rail_points(o)
    assert min(math.dist((t.x, t.y), p) for t in o.trees for p in pts) > o.canopy + 0.5


def test_every_tree_is_close_to_the_rail():
    o = Orchard()
    pts = _rail_points(o)
    assert max(min(math.dist((t.x, t.y), p) for p in pts) for t in o.trees) <= o.row_gap / 2 + 0.01


def test_rail_is_a_closed_loop():
    o = Orchard()
    assert o.route[0] == o.route[-1]


def test_point_at_wraps_around():
    o = Orchard()
    assert o.point_at(o.rail_length + 1) == o.point_at(1)
