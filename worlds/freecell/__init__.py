from collections import Counter
from typing import Any, Dict, List

from BaseClasses import Region, Tutorial
from worlds.AutoWorld import WebWorld, World

from . import items, locations
from .options import FreeCellOptions


class FreeCellWebWorld(WebWorld):
    theme = "partyTime"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up FreeCell. This guide covers multiworld, and website.",
            "English",
            "setup_en.md",
            "setup/en",
            ["alphabeth_"],
        )
    ]


class FreeCellWorld(World):
    """
    FreeCell solitaire with a handicap: free cells, tableau columns, suit foundations and undo
    are locked until you find them. Every game is a random deal; you earn checks by reaching
    score thresholds (stacked cards, cards on the foundation and complete suits).
    """
    game = items.GAME_NAME
    web = FreeCellWebWorld()

    options_dataclass = FreeCellOptions
    options: FreeCellOptions

    topology_present = False

    item_name_to_id = items.item_name_to_id
    item_name_groups = items.item_name_groups
    location_name_to_id = locations.location_name_to_id
    location_name_groups = locations.location_name_groups

    precollected_counts: Dict[str, int]

    # ------------------------------------------------------------------
    def generate_early(self) -> None:
        opts = self.options
        score_count = len(locations.score_steps(opts.score_step.value))

        # starting foundations
        precollected: Counter = Counter(
            self.random.sample(items.FOUNDATION_ITEMS, opts.starting_foundations.value))

        # With a large score step there are fewer locations than real items. Hand the surplus to
        # the player at the start (least important first) so the game stays beatable.
        counts = items.get_item_counts(opts.start_free_cells.value, opts.start_tableau_columns.value)
        remaining: List[str] = []
        for name in ["Undo", "Free Cell", "Tableau Column", *items.FOUNDATION_ITEMS]:
            remaining.extend([name] * max(0, counts.get(name, 0) - precollected.get(name, 0)))
        overflow = len(remaining) - score_count
        if overflow > 0:
            precollected.update(remaining[:overflow])

        self.precollected_counts = dict(precollected)
        for name, count in precollected.items():
            for _ in range(count):
                self.multiworld.push_precollected(self.create_item(name))

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        locations.add_locations(menu, self.player, self.options.score_step.value,
                                self.options.start_free_cells.value,
                                self.options.start_tableau_columns.value)
        self.multiworld.regions.append(menu)

    def create_items(self) -> None:
        location_count = len(self.multiworld.get_unfilled_locations(self.player))
        self.multiworld.itempool += items.create_item_pool(
            self.player, location_count,
            self.options.start_free_cells.value, self.options.start_tableau_columns.value,
            self.precollected_counts)

    def set_rules(self) -> None:
        # Access rules are attached to the locations in locations.add_locations.
        goal = locations.GOAL_LOCATION_NAME
        self.multiworld.completion_condition[self.player] = \
            lambda state: state.can_reach_location(goal, self.player)

    # ------------------------------------------------------------------
    def create_item(self, name: str) -> items.FreeCellItem:
        return items.create_item(self.player, name)

    def get_filler_item_name(self) -> str:
        return items.FILLER_ITEM_NAME

    def fill_slot_data(self) -> Dict[str, Any]:
        # read by archipelago.js
        return {
            "start_free_cells": self.options.start_free_cells.value,
            "start_tableau": self.options.start_tableau_columns.value,
            "score_step": self.options.score_step.value,
        }
