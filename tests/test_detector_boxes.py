from durian.detector import drop_nested


def test_partial_box_inside_fruit_is_dropped():
    dets = [([0, 0, 100, 100], 0.5), ([10, 10, 40, 40], 0.3)]
    assert drop_nested(dets) == [([0, 0, 100, 100], 0.5)]


def test_box_spanning_two_fruits_is_dropped():
    left, right = ([0, 0, 50, 50], 0.5), ([55, 0, 105, 50], 0.5)
    merged = ([0, 0, 105, 50], 0.4)
    assert drop_nested([left, right, merged]) == [left, right]


def test_separate_fruits_are_kept():
    dets = [([0, 0, 50, 50], 0.5), ([60, 0, 110, 50], 0.5)]
    assert drop_nested(dets) == dets
