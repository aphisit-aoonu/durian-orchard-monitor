"""How hard a durian hits whatever catches it. Plain kinematics, no bruise model.

Speed after a fall of h metres: v = sqrt(2 g h).
Average deceleration when stopped over a distance d: a = v^2 / (2 d).
"""
import math
from dataclasses import dataclass

G = 9.81


@dataclass(frozen=True)
class Catch:
    name: str
    fall_m: float        # free fall before first contact
    stop_m: float        # distance over which it is brought to a stop (net sag, bag stretch, soil give)
    exit_speed: float = 0.0  # if it then travels on (e.g. down a braked tube), the speed it arrives at the basket

    def impact_speed(self) -> float:
        return math.sqrt(2 * G * self.fall_m)

    def peak_g(self) -> float:
        """Average deceleration during the stop, in g. Real peaks are higher; this is for comparison."""
        v = self.impact_speed()
        return v * v / (2 * self.stop_m) / G

    def energy_j(self, mass_kg: float) -> float:
        return mass_kg * G * self.fall_m


def pole_length(fruit_height_m: float, offset_m: float, mount_height_m: float = 1.0) -> float:
    """Straight pole from the mount on the cart to a fruit offset_m to the side of the rail."""
    return math.hypot(offset_m, fruit_height_m - mount_height_m)


def load_moment_nm(load_kg: float, offset_m: float) -> float:
    """Tipping moment about the rail from the fruit alone, held offset_m to the side."""
    return load_kg * G * offset_m


def scenarios(fruit_height_m: float, net_height_m: float = 2.0) -> list[Catch]:
    """The three options compared in the demo, for a fruit hanging at fruit_height_m."""
    return [
        Catch("ground", fruit_height_m, 0.02),
        Catch("net", fruit_height_m - net_height_m, 0.5),
        Catch("bag", 0.3, 0.1, exit_speed=1.0),
    ]
