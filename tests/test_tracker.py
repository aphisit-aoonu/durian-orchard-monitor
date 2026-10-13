import numpy as np

from durian.motion import apply
from durian.tracker import Tracker


def test_same_fruit_keeps_one_id_and_counts_once():
    tr = Tracker()
    for _ in range(4):
        tr.update([([100, 100, 160, 170], 0.5)])
    assert tr.unique_count == 1
    assert [t.id for t in tr.tracks] == [1]


def test_two_fruits_count_twice():
    tr = Tracker()
    for _ in range(3):
        tr.update([([100, 100, 160, 170], 0.5), ([300, 100, 360, 170], 0.5)])
    assert tr.unique_count == 2


def test_single_glitch_is_not_counted():
    tr = Tracker()
    tr.update([([500, 500, 520, 520], 0.3)])
    for _ in range(10):
        tr.update([])
    assert tr.unique_count == 0


def test_fruit_lowered_on_a_rope_is_flagged_once():
    tr = Tracker()
    events = []
    for k in range(8):
        y = 100 + 40 * k
        events += tr.update([([100, y, 160, y + 70], 0.5)])
    assert len(events) == 1
    assert tr.unique_count == 1


def test_apply_translation():
    shift = np.array([[1, 0, 10], [0, 1, -5], [0, 0, 1]], dtype=float)
    assert apply(shift, [0, 0, 10, 10]) == [10, -5, 20, 5]


def test_lowered_fruit_keeps_its_id_through_a_fast_drop():
    tr = Tracker()
    events = []
    for k in range(6):
        y = 100 + 40 * k
        events += tr.update([([100, y, 160, y + 70], 0.5)])
    events += tr.update([([105, 600, 165, 670], 0.5)])  # big jump down the rope
    assert len(events) == 1
    assert [t.id for t in tr.tracks] == [1]


def test_rope_fruit_split_into_two_tracks_is_merged_back():
    tr = Tracker()
    events = []
    for k in range(6):
        y = 100 + 40 * k
        events += tr.update([([100, y, 160, y + 70], 0.5)])
    # the old track grabs a small box near the rope while the real fruit appears further down
    for k in range(6):
        y = 420 + 50 * k
        events += tr.update([([110, 330, 150, 360], 0.4), ([100, y, 160, y + 70], 0.5)])
    assert len(events) == 1
