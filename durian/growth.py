"""Tree height against the machine's reach, and days left until each tree's fruit is due."""
from dataclasses import dataclass
from datetime import date, timedelta

REACH_M = 6.0            # trees are topped to stay under this, so a short pole reaches every fruit
WARN_MARGIN_M = 0.5      # closer than this to the limit: top it after this harvest
DAYS_TO_HARVEST = 120    # Monthong, days after full bloom


@dataclass(frozen=True)
class TreeState:
    id: str
    height_m: float
    growth_m_per_year: float
    bloom: date | None = None   # full bloom of this season's crop, None if the tree is not carrying fruit

    def height_after(self, days: int) -> float:
        return self.height_m + self.growth_m_per_year * days / 365

    def status(self, reach_m: float = REACH_M) -> str:
        if self.height_m > reach_m:
            return "over"
        return "soon" if self.height_m > reach_m - WARN_MARGIN_M else "ok"

    def days_until_over(self, reach_m: float = REACH_M) -> int | None:
        """Days until it outgrows the reach at its current rate. 0 if it already has, None if it is not growing."""
        if self.height_m > reach_m:
            return 0
        if self.growth_m_per_year <= 0:
            return None
        return int((reach_m - self.height_m) / self.growth_m_per_year * 365) + 1

    def harvest_date(self, days: int = DAYS_TO_HARVEST) -> date | None:
        return self.bloom + timedelta(days=days) if self.bloom else None

    def days_to_harvest(self, today: date, days: int = DAYS_TO_HARVEST) -> int | None:
        """Negative means overdue."""
        due = self.harvest_date(days)
        return (due - today).days if due else None


def due_in_week(trees: list[TreeState], week_start: date) -> list[TreeState]:
    """Trees whose fruit comes due in the seven days from week_start, earliest first."""
    end = week_start + timedelta(days=7)
    hits = [t for t in trees if t.bloom and week_start <= t.harvest_date() < end]
    return sorted(hits, key=lambda t: t.harvest_date())
