from PySide6.QtGui import QColor, QKeySequence

from pathlib import Path
import tomllib
from paths import SETTINGS
from dataclasses import dataclass


@dataclass
class Keybinds:
    auto_note: list[QKeySequence]
    hint: list[QKeySequence]
    apply_hint: list[QKeySequence]
    solve: list[QKeySequence]
    remove: list[QKeySequence]

    up: list[QKeySequence]
    down: list[QKeySequence]
    left: list[QKeySequence]
    right: list[QKeySequence]

    # Maps each of the 9 numbers to the key sequence needed to input them
    numbers: dict[int, list[QKeySequence]]

    puzzle_menu: list[QKeySequence]

    def __post_init__(self):
        keys = []

        for name, val in self.__dict__.items():
            if name == "numbers":
                if not isinstance(val, dict):
                    raise ValueError("Number keybinds must be under [keybinds.numbers]")
                for k, v in val.items():
                    keys += v
                    if not isinstance(k, int):
                        raise ValueError(
                            f"Key {k} is invalid. Keys for [keybinds.numbers] should be a number"
                        )
                    if not 1 <= k <= 9:
                        raise ValueError(
                            f"Key {k} is invalid. Keys for [keybinds.numbers] must be between 1 and 9 inclusive"
                        )
                    if not isinstance(v, list):
                        raise ValueError(
                            f"Value for key {k} is invalid. Values for [keybinds.numbers] should be a list"
                        )
                    for k in v:
                        if not isinstance(k, QKeySequence):
                            raise ValueError(
                                f"Value for key {k} is invalid. [keybinds.numbers] keybind failed to be interpreted"
                            )

            else:
                keys += val
                if not isinstance(val, list):
                    raise ValueError(
                        f"Value for key {name} under [keybinds] is invalid. Must be a list."
                    )
                for x in val:
                    if not isinstance(x, QKeySequence):
                        raise ValueError(
                            f"Value for key {name} under [keybinds] is invalid. Must be a list."
                        )

        if len(keys) > len(set(keys)):
            raise ValueError("Duplicate keybindings detected")


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

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if not isinstance(val, QColor):
                raise ValueError(
                    f"Value for key {name} under [colours] is invalid. Failed to convert to QColor."
                )


@dataclass
class Sizes:
    border: int
    big_border: int
    cell: int
    text: int

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if not isinstance(val, int):
                raise ValueError(
                    f"Value for key {name} under [sizes] is invalid. Must be an integer."
                )

            if val <= 0:
                raise ValueError(
                    f"Value for key {name} under [sizes] is invalid. Must be more than 0."
                )


@dataclass
class Gameplay:
    auto_note: bool
    start_full: bool

    def __post_init__(self):
        for key, value in self.__dict__.items():
            if not isinstance(value, bool):
                raise ValueError(
                    f"Value for key {key} under [gameplay] is invalid. Must be bool."
                )


@dataclass
class Developer:
    port: int

    def __post_init__(self):
        if not isinstance(self.port, int):
            raise TypeError(
                "Value for key port under [developer] is invalid. Must be an integer"
            )

        if not 0 <= self.port <= 65535:
            # Port number should also be unused by other processes
            # This is not checked here but error will be given on app launch
            raise ValueError(
                "Value for key port under [developer] is invalid. Must be between 0 and 65535 (inclusive)."
            )


@dataclass
class Settings:
    keybinds: Keybinds
    colours: Colours
    sizes: Sizes
    gameplay: Gameplay
    developer: Developer

    def __post_init__(self):
        # If the other dataclasses fail it's probably a user error with an invalid .toml file.
        # These should never fail even with an invalid .toml. If they do it is a developer error.
        if not isinstance(self.keybinds, Keybinds):
            raise ValueError("keybinds must be of type Keybinds")
        if not isinstance(self.colours, Colours):
            raise ValueError("colours must be of type Colours")
        if not isinstance(self.sizes, Sizes):
            raise ValueError("sizes must be of type Sizes")
        if not isinstance(self.gameplay, Gameplay):
            raise ValueError("gameplay must be of type Gameplay")
        if not isinstance(self.developer, Developer):
            raise ValueError("developer must be of type Developer")


# TODO: set some default values


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
            gameplay=Gameplay(**data["gameplay"]),
            developer=Developer(**data["developer"]),
        )
    except Exception as e:
        # Catches missing settings keys, invalid settings keys and anything that fails the parsing funcs
        raise e from ValueError(f"Invalid {path.absolute()}")


settings = load_settings()
# TODO: Don't let anyone import anything besides this
