from dataclasses import dataclass

from Options import PerGameCommonOptions, Range


class ScoreStep(Range):
    """
    With a step of 5 you get the checks Score 5, 10, 15 ... 90 plus the goal Score 92 (19 checks).
    A step of 1 gives 92 checks. A higher step gives fewer checks and a shorter game.
    Reaching Score 92 (all cards on the foundations) is always the goal.
    """
    display_name = "Score Step"
    range_start = 1
    range_end = 10
    default = 5


class StartFreeCells(Range):
    """Number of free cells (of 4) you can use without finding Free Cell items."""
    display_name = "Starting Free Cells"
    range_start = 0
    range_end = 4
    default = 1


class StartTableauColumns(Range):
    """Number of tableau columns (of 8) that are unlocked without finding Tableau Column items."""
    display_name = "Starting Tableau Columns"
    range_start = 2
    range_end = 8
    default = 4


class StartingFoundations(Range):
    """Number of random suit foundations that you start with."""
    display_name = "Starting Foundations"
    range_start = 0
    range_end = 4
    default = 0


@dataclass
class FreeCellOptions(PerGameCommonOptions):
    score_step: ScoreStep
    start_free_cells: StartFreeCells
    start_tableau_columns: StartTableauColumns
    starting_foundations: StartingFoundations
