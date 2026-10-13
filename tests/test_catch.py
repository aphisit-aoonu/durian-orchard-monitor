import math

import pytest

from durian.catch import Catch, load_moment_nm, pole_length, scenarios


def test_pole_to_a_topped_tree_is_much_shorter_than_to_a_tall_one():
    assert pole_length(4, 3) == pytest.approx(math.hypot(3, 3))
    assert pole_length(5, 5) == pytest.approx(6.4, abs=0.05)
    assert pole_length(10, 5) == pytest.approx(10.3, abs=0.05)


def test_load_moment_depends_on_sideways_offset():
    assert load_moment_nm(3, 5) == pytest.approx(3 * 9.81 * 5)


def test_ten_metre_fall_is_fourteen_metres_per_second():
    assert Catch("x", 10, 0.1).impact_speed() == pytest.approx(math.sqrt(2 * 9.81 * 10))
    assert Catch("x", 10, 0.1).impact_speed() == pytest.approx(14.0, abs=0.05)


def test_longer_stop_means_gentler_catch():
    assert Catch("soft", 5, 0.5).peak_g() < Catch("hard", 5, 0.05).peak_g()


def test_peak_g_equals_height_over_stop_distance():
    # v^2 / (2 d g) = 2 g h / (2 d g) = h / d
    assert Catch("x", 8, 0.5).peak_g() == pytest.approx(16.0)


def test_bag_at_cutter_is_far_gentler_than_ground():
    ground, net, bag = scenarios(10.0)
    assert bag.impact_speed() < net.impact_speed() < ground.impact_speed()
    assert bag.peak_g() < net.peak_g() < ground.peak_g()


def test_energy_scales_with_mass_and_height():
    assert Catch("x", 10, 0.1).energy_j(3) == pytest.approx(3 * 9.81 * 10)
