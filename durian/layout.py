"""Orchard layout and monorail route, in metres. Used by the plan drawing and the simulation."""
import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tree:
    id: str
    x: float
    y: float
    row: int


@dataclass
class Orchard:
    cols: int = 8               # trees per row
    rows: int = 6
    tree_gap: float = 9.0       # metres between trees in a row
    row_gap: float = 10.0       # metres between rows
    margin: float = 8.0
    canopy: float = 3.6         # canopy radius
    trees: list[Tree] = field(default_factory=list)
    route: list[tuple[float, float]] = field(default_factory=list)  # rail polyline
    depot: tuple[float, float] = (0, 0)
    collection: tuple[float, float] = (0, 0)

    def __post_init__(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self.trees.append(Tree(f"{chr(65 + r)}{c + 1}", self.margin + c * self.tree_gap,
                                       self.margin + r * self.row_gap, r))
        # the rail runs down every second alley, so each pass serves the row above and below it
        x0 = self.margin - self.tree_gap * 0.6
        x1 = self.margin + (self.cols - 1) * self.tree_gap + self.tree_gap * 0.6
        alleys = [self.margin + (r + 0.5) * self.row_gap for r in range(0, self.rows - 1, 2)]
        start = (x0 - 14, alleys[0])
        # both sit at the end of the rail: the cart unloads, then parks to charge
        self.collection = (start[0] - 3, start[1] - 4.5)
        self.depot = (start[0] - 3, start[1] + 4.5)
        self.route = [start]
        for k, y in enumerate(alleys):
            a, b = (x0, x1) if k % 2 == 0 else (x1, x0)
            self.route += [(a, y), (b, y)]
        # back to the depot outside the last row, then up the outer edge
        last = self.route[-1]
        edge_x = x0 - 3
        outside = self.margin + (self.rows - 1) * self.row_gap + self.row_gap * 0.5
        if abs(last[0] - x1) < 1e-6:
            self.route += [(x1, outside), (edge_x, outside)]
        else:
            self.route += [(edge_x, last[1])]
        self.route += [(edge_x, start[1]), start]

    @property
    def width(self) -> float:
        return 2 * self.margin + (self.cols - 1) * self.tree_gap

    @property
    def height(self) -> float:
        return 2 * self.margin + (self.rows - 1) * self.row_gap

    @property
    def rail_length(self) -> float:
        return sum(math.dist(a, b) for a, b in zip(self.route, self.route[1:]))

    def point_at(self, s: float) -> tuple[float, float]:
        """Position on the rail after travelling s metres from the start (wraps around)."""
        s %= self.rail_length
        for a, b in zip(self.route, self.route[1:]):
            seg = math.dist(a, b)
            if s <= seg:
                f = s / seg if seg else 0
                return a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f
            s -= seg
        return self.route[-1]

    def stop_for(self, tree: Tree) -> float:
        """Distance along the rail where the cart is level with this tree."""
        best, best_s, s = 1e9, 0.0, 0.0
        for a, b in zip(self.route, self.route[1:]):
            seg = math.dist(a, b)
            for k in range(41):
                f = k / 40
                p = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
                d = math.dist(p, (tree.x, tree.y))
                if d < best:
                    best, best_s = d, s + seg * f
            s += seg
        return best_s
