from typing import Dict, List, NamedTuple, Optional, Set

from BaseClasses import Item, ItemClassification

GAME_NAME = "FreeCell"

# Item ids = BASE_ID + code. archipelago.js uses the same numbers (ITEM_BASE_ID).
BASE_ID = 7_700_000

MAX_FREE_CELLS = 4
MAX_COLUMNS = 8
DEFAULT_START_FREE_CELLS = 1
DEFAULT_START_COLUMNS = 4

SUITS: List[str] = ["Hearts", "Clubs", "Diamonds", "Spades"]  # same order as the suit index in the game
FOUNDATION_ITEMS: List[str] = [f"{suit} Foundation" for suit in SUITS]


class FreeCellItem(Item):
    game = GAME_NAME


class FreeCellItemData(NamedTuple):
    code: int
    classification: ItemClassification
    max_count: int = 1  # maximum number that can ever be in the pool (see get_item_counts)


item_table: Dict[str, FreeCellItemData] = {
    # --- progression ---
    "Free Cell": FreeCellItemData(BASE_ID + 1, ItemClassification.progression, MAX_FREE_CELLS),
    "Tableau Column": FreeCellItemData(BASE_ID + 2, ItemClassification.progression, MAX_COLUMNS),
    "Hearts Foundation": FreeCellItemData(BASE_ID + 10, ItemClassification.progression),
    "Clubs Foundation": FreeCellItemData(BASE_ID + 11, ItemClassification.progression),
    "Diamonds Foundation": FreeCellItemData(BASE_ID + 12, ItemClassification.progression),
    "Spades Foundation": FreeCellItemData(BASE_ID + 13, ItemClassification.progression),
    # --- useful ---
    "Undo": FreeCellItemData(BASE_ID + 3, ItemClassification.useful),
    # --- filler (needed because there are far more locations than real items) ---
    "Filler Card": FreeCellItemData(BASE_ID + 100, ItemClassification.filler, 0),
}

item_name_to_id: Dict[str, int] = {name: data.code for name, data in item_table.items()}

item_name_groups: Dict[str, Set[str]] = {
    "Foundations": set(FOUNDATION_ITEMS),
}

FILLER_ITEM_NAME = "Filler Card"


def get_item_counts(start_free_cells: int = DEFAULT_START_FREE_CELLS,
                    start_columns: int = DEFAULT_START_COLUMNS) -> Dict[str, int]:
    """
    How many of each real item go into the pool.

    The player always has `start_free_cells` free cells and `start_columns` tableau columns
    without any item (these base values are sent to the client in slot_data), so only the
    remainder is shuffled into the multiworld.
    """
    start_free_cells = max(0, min(MAX_FREE_CELLS, start_free_cells))
    start_columns = max(1, min(MAX_COLUMNS, start_columns))

    counts: Dict[str, int] = {
        "Free Cell": MAX_FREE_CELLS - start_free_cells,
        "Tableau Column": MAX_COLUMNS - start_columns,
        "Undo": 1,
    }
    for name in FOUNDATION_ITEMS:
        counts[name] = 1
    return {name: count for name, count in counts.items() if count > 0}


def create_item(player: int, name: str) -> FreeCellItem:
    data = item_table[name]
    return FreeCellItem(name, data.classification, data.code, player)


def create_item_pool(player: int, location_count: int,
                     start_free_cells: int = DEFAULT_START_FREE_CELLS,
                     start_columns: int = DEFAULT_START_COLUMNS,
                     precollected: Optional[Dict[str, int]] = None) -> List[FreeCellItem]:
    """
    Builds the full pool: every real item (minus the precollected ones, which are already in the
    start inventory) padded with filler so that #items == #locations.
    """
    precollected = precollected or {}
    pool: List[FreeCellItem] = []
    for name, count in get_item_counts(start_free_cells, start_columns).items():
        pool.extend(create_item(player, name) for _ in range(max(0, count - precollected.get(name, 0))))

    filler_needed = location_count - len(pool)
    if filler_needed < 0:
        raise Exception(f"FreeCell: {len(pool)} items but only {location_count} locations.")
    pool.extend(create_item(player, FILLER_ITEM_NAME) for _ in range(filler_needed))
    return pool
