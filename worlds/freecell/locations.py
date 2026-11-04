from typing import Callable, Dict, List, NamedTuple

from BaseClasses import CollectionState, Location, Region

from .items import (
    BASE_ID, DEFAULT_START_COLUMNS, DEFAULT_START_FREE_CELLS, FOUNDATION_ITEMS, GAME_NAME,
)

# Every game is a fully random deal. The locations are SCORE THRESHOLDS inside that deal:
#
#   +1 point  for every card stacked on a fitting card in a tableau column
#             (one rank lower, other colour; cards in locked columns don't score)
#   +1 point  for every card on a foundation
#   +10 bonus for every suit that is completely (A to K) on a foundation
#
# The score is calculated from the board state, so it can go down again (breaking a stack),
# but reaching a threshold stays checked. The maximum is 52 + 4 * 10 = 92 = deal won.
#
# The player chooses a score step (option `score_step`): a step of 5 gives the locations
# "Score 5", "Score 10", ... "Score 90" plus the goal "Score 92". A smaller step means more checks.
#
# Location id = LOCATION_BASE_ID + score, for EVERY score 1..92 (so the data package is static
# and the step can be changed freely). The generator only creates the thresholds that belong to
# the chosen step; the client ignores the other ids. archipelago.js uses the same formula.
LOCATION_BASE_ID = BASE_ID

MAX_SCORE = 92
GOAL_LOCATION_NAME = f"Score {MAX_SCORE}"  # all 52 cards on the foundations


class FreeCellLocation(Location):
    game = GAME_NAME


def score_location_name(score: int) -> str:
    return f"Score {score}"


def score_steps(step: int) -> List[int]:
    """Thresholds for a given step; the maximum score (the goal) is always included."""
    step = max(1, step)
    return list(range(step, MAX_SCORE, step)) + [MAX_SCORE]


location_name_to_id: Dict[str, int] = {
    score_location_name(score): LOCATION_BASE_ID + score for score in range(1, MAX_SCORE + 1)
}

location_name_groups: Dict[str, set] = {
    "Score": set(location_name_to_id),
}


# ---------------------------------------------------------------------------
# Access rules
# ---------------------------------------------------------------------------
class Requirement(NamedTuple):
    foundations: int = 0   # number of different suit-foundation items
    free_cells: int = 0    # total free cells (base + items)
    columns: int = 0       # total tableau columns (base + items)


def requirement_for(score: int) -> Requirement:
    """
    Heuristic: higher scores need more suits on the foundation, more free cells and more columns.
    Deals are random, so there is no per-deal solver logic - tune this after playtesting.
    Scores up to 10 need nothing, so sphere 1 is never empty.
    """
    if score >= MAX_SCORE:
        return Requirement(foundations=4, free_cells=4, columns=8)
    if score <= 10:
        return Requirement()
    foundations = 1 if score <= 30 else 2 if score <= 50 else 3 if score <= 70 else 4
    free_cells = min(4, 1 + score // 25)
    columns = min(8, 4 + (score - 10) // 10)
    return Requirement(foundations, free_cells, columns)


def make_rule(score: int, player: int, start_free_cells: int,
              start_columns: int) -> Callable[[CollectionState], bool]:
    req = requirement_for(score)

    def rule(state: CollectionState) -> bool:
        if req.foundations and sum(state.has(item, player) for item in FOUNDATION_ITEMS) < req.foundations:
            return False
        if start_free_cells + state.count("Free Cell", player) < req.free_cells:
            return False
        if start_columns + state.count("Tableau Column", player) < req.columns:
            return False
        return True

    return rule


def add_locations(region: Region, player: int, step: int,
                  start_free_cells: int = DEFAULT_START_FREE_CELLS,
                  start_columns: int = DEFAULT_START_COLUMNS) -> List[FreeCellLocation]:
    """Adds one location per score threshold of `step` to `region` and returns them."""
    created: List[FreeCellLocation] = []
    for score in score_steps(step):
        location = FreeCellLocation(player, score_location_name(score), LOCATION_BASE_ID + score, region)
        location.access_rule = make_rule(score, player, start_free_cells, start_columns)
        region.locations.append(location)
        created.append(location)
    return created
