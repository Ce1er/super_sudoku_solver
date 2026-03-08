from typing import Any
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtCore import Qt

from pathlib import Path
import tomllib
from paths import SETTINGS
from dataclasses import dataclass

# # TODO:: I feel like this would be better as .toml
#
# # Each highlight group's corresponding rgba colour. These are for hints.
# highlight_colours: dict[int, QColor] = {1: QColor(248, 252, 3, 255)}
#
# number_colour: QColor = QColor(0, 0, 0, 255)
# candidate_colour = QColor(30, 50, 78, 255)
# special_candidate_colour = QColor(25, 1, 98, 255)
# rejected_candidate_colour = QColor(255, 0, 0, 255)
#
# border_colour: QColor = QColor(0, 0, 0, 255)
# big_border_colour: QColor = QColor(0, 0, 0, 255)
# background_colour: QColor = QColor(255, 255, 255, 255)
# text_colour: QColor = QColor(0, 0, 0, 255)
#
#
# border_size: int = 1
# big_border_size: int = 3
# cell_size: int = 60
#
#
# remove_cell: list[Qt.Key] = [Qt.Key_Backspace]
# add_cell: dict[int, list[Qt.Key]] = {
#     1: [Qt.Key_1],
#     2: [Qt.Key_2],
#     3: [Qt.Key_3],
#     4: [Qt.Key_4],
#     5: [Qt.Key_5],
#     6: [Qt.Key_6],
#     7: [Qt.Key_7],
#     8: [Qt.Key_8],
#     9: [Qt.Key_9],
# }
# auto_note: list[Qt.Key] = [Qt.Key_N]
# select_left: list[Qt.Key]
# select_right: list[Qt.Key]
# select_up: list[Qt.Key]
# select_down: list[Qt.Key]
#
#
# with SETTINGS.open("rb") as f:
#     toml = tomllib.load(f)
#
# port = toml["advanced"]["port"]


@dataclass
class Keybinds:
    auto_note: list[QKeySequence]
    hint: list[QKeySequence]
    apply_hint: list[QKeySequence]
    solve: list[QKeySequence]
    remove:list[QKeySequence]

    up: list[QKeySequence]
    down: list[QKeySequence]
    left: list[QKeySequence]
    right: list[QKeySequence]

    # Maps each of the 9 numbers to the key sequence needed to input them
    numbers: dict[int, list[QKeySequence]]

    puzzle_menu: list[QKeySequence]


@dataclass
class Colours:
    clue: QColor
    guess: QColor
    candidate: QColor
    special_candidate: QColor
    rejected_candidate: QColor
    border: QColor
    big_border: QColor
    background: QColor
    text: QColor


@dataclass
class Sizes:
    border: int
    big_border: int
    cell: int
    text: int


@dataclass
class Developer:
    port: int


@dataclass
class Settings:
    keybinds: Keybinds
    colours: Colours
    sizes: Sizes
    developer: Developer


# TODO: __post_init__ validation
# or maybe it is better to handle earlier
# and set some defaults


def parse_sequences(seq_list: list[str]) -> list[QKeySequence]:
    return [QKeySequence(x) for x in seq_list]


def parse_normal_input(data: dict[str, list[str]]) -> dict[str, list[QKeySequence]]:
    result = {}

    for key, seqs in data.items():
        result[key] = parse_sequences(seqs)

    return result


def parse_number_input(data: dict[int, list[str]]) -> dict[int, list[QKeySequence]]:
    result = {}

    for num, seqs in data.items():
        result[int(num)] = parse_sequences(seqs)

    return result


def parse_colours(data: dict[str, list[int]]) -> dict[str, QColor]:
    result = {}

    for part, colour in data.items():
        result[part] = QColor(*colour)

    return result


def load_settings(path: Path = SETTINGS) -> Settings:
    with path.open("rb") as f:
        data = tomllib.load(f)

    try:
        return Settings(
            keybinds=Keybinds(
                **parse_normal_input(
                    dict(
                        filter(lambda x: x[0] != "numbers", data["keybindings"].items())
                    )
                ),
                numbers=parse_number_input(data["keybindings"]["numbers"]),
            ),
            colours=Colours(**parse_colours(data["colours"])),
            sizes=Sizes(**data["sizes"]),
            developer=Developer(**data["developer"]),
        )
    except Exception as e:
        # Catches missing settings keys, invalid settings keys and anything that fails the parsing funcs
        raise e from ValueError(f"Invalid {path.absolute()}")


settings = load_settings()
# TODO: Don't let anyone import anything besides this
