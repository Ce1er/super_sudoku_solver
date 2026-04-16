from typing import Optional
from PySide6.QtGui import QColor, QKeySequence

from pathlib import Path
import tomllib
from super_sudoku_solver.paths import SETTINGS
from dataclasses import dataclass, field


# These should be immutable because hot config reloading is not supported
@dataclass(frozen=True)
class Keybinds:
    _DEFAULT_NUMBERS = {
        k: [QKeySequence(str(k)), QKeySequence(f"Num+{k}")] for k in range(1, 10)
    }

    auto_note: list[QKeySequence] = field(default_factory=list)
    hint: list[QKeySequence] = field(default_factory=list)
    apply_hint: list[QKeySequence] = field(default_factory=list)
    solve: list[QKeySequence] = field(default_factory=list)
    reset: list[QKeySequence] = field(default_factory=list)

    up: list[QKeySequence] = field(default_factory=list)
    down: list[QKeySequence] = field(default_factory=list)
    left: list[QKeySequence] = field(default_factory=list)
    right: list[QKeySequence] = field(default_factory=list)

    # Maps each of the 9 numbers to the key sequence needed to input them
    _numbers: dict[int, list[QKeySequence]] = field(default_factory=dict)

    toggle_mode: list[QKeySequence] = field(default_factory=list)

    @property
    def numbers(self):
        # Allows user to override some number keybinds without losing defaults
        # for any that weren't overwritten
        return self._DEFAULT_NUMBERS | self._numbers

    def __post_init__(self):
        keys = []

        for name, val in self.__dict__.items():
            if name == "_numbers":
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


@dataclass(frozen=True)
class Colours:
    _DEFAULT_HINT_HIGHLIGHT = {
        1: QColor("#dc8a78"),
        2: QColor("#8839ef"),
    }
    clue: QColor = field(default_factory=lambda: QColor(0, 0, 0, 255))
    guess: QColor = field(default_factory=lambda: QColor(0, 0, 0, 255))
    candidate: QColor = field(default_factory=lambda: QColor(30, 50, 78, 255))
    border: QColor = field(default_factory=lambda: QColor(0, 0, 0, 255))
    big_border: QColor = field(default_factory=lambda: QColor(0, 0, 0, 255))
    background: QColor = field(default_factory=lambda: QColor(255, 255, 255, 255))
    board_background: QColor = field(default_factory=lambda: QColor(0, 0, 0, 0))
    menu_background: QColor = field(default_factory=lambda: QColor(255, 255, 255, 255))
    button_background: QColor = field(
        default_factory=lambda: QColor(255,255, 255, 255)
    )
    hint_background: QColor = field(default_factory=lambda: QColor(0, 0, 0, 0))
    message_background: QColor = field(
        default_factory=lambda: QColor(255, 255, 255, 255)
    )
    text: QColor = field(default_factory=lambda: QColor(0, 0, 0, 255))

    selected: QColor = field(default_factory=lambda: QColor(0, 0, 255, 100))
    adjacent: QColor = field(default_factory=lambda: QColor(0, 0, 170, 50))

    _hint_highlight: dict[int, list[QColor]] = field(default_factory=dict)

    @property
    def hint_highlight(self):
        # Allows user to override some hint highlights without losing defaults
        # for any that weren't overwritten
        print("foo", self._DEFAULT_HINT_HIGHLIGHT|self._hint_highlight)
        return self._DEFAULT_HINT_HIGHLIGHT | self._hint_highlight

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if name == "_hint_highlight":
                if not isinstance(val, dict):
                    raise ValueError(
                        "Hint highlights must be under [colours.hint-highlights]"
                    )
            else:
                if not isinstance(val, QColor):
                    raise ValueError(
                        f"Value for key {name} under [colours] is invalid. Failed to convert to QColor."
                    )
                if not val.isValid():
                    raise ValueError(
                        f"Value for key {name} under [colours] is invalid. Failed to convert to valid QColor."
                    )


@dataclass(frozen=True)
class Sizes:
    border: int = field(default=1)
    big_border: int = field(default=3)
    cell: int = field(default=60)
    text: int = field(default=11)
    margin: int = field(default=50)
    # All other sizes are calculated based on cell size

    def __post_init__(self):
        return
        for name, val in self.__dict__.items():
            if not isinstance(val, int):
                raise ValueError(
                    f"Value for key {name} under [sizes] is invalid. Must be an integer."
                )

            if val <= 0:
                raise ValueError(
                    f"Value for key {name} under [sizes] is invalid. Must be more than 0."
                )


@dataclass(frozen=True)
class Gameplay:
    auto_note: bool = field(default=True)
    start_full: bool = field(default=True)

    def __post_init__(self):
        for key, value in self.__dict__.items():
            if not isinstance(value, bool):
                raise ValueError(
                    f"Value for key {key} under [gameplay] is invalid. Must be bool."
                )

        if not self.start_full:
            raise NotImplementedError(
                "Board must start full so candidates contain solution"
            )
        if not self.auto_note:
            raise NotImplementedError("Techniques rely on board being auto_noted")


@dataclass(frozen=True)
class Developer:
    port: int = field(default=46215)

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


@dataclass(frozen=True)
class Settings:
    keybinds: Keybinds = field(default_factory=lambda: Keybinds())
    colours: Colours = field(default_factory=lambda: Colours())
    sizes: Sizes = field(default_factory=lambda: Sizes())
    gameplay: Gameplay = field(default_factory=lambda: Gameplay())
    developer: Developer = field(default_factory=lambda: Developer())

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


def parse_keybind_input(data: dict[str, list[str]]) -> dict[str, list[QKeySequence]]:
    result = {}

    for key, seqs in data.items():
        result[key] = parse_sequences(seqs)

    return result


def parse_number_input(data: dict[int, list[str]]) -> dict[int, list[QKeySequence]]:
    result = {}

    for num, seqs in data.items():
        result[int(num)] = parse_sequences(seqs)

    return result

def parse_hint_highlight(data: dict[int, list[int]]) -> dict[int, list[QColor]]:
    result = {}

    for num, colour in data.items():
        print(num,colour)
        result[int(num)] = QColor(*colour)

    return result


def parse_colours(data: dict[str, list[int]]) -> dict[str, QColor]:
    result = {}

    for part, colour in data.items():
        result[part] = QColor(*colour)

    return result


def load_settings(path: Optional[Path] = None) -> Settings:
    """
    Load settings from path if given or fallback to defaults.
    """
    if path is not None:
        with path.open("rb") as f:
            data = tomllib.load(f)
    else:
        return Settings()

    try:
        user_settings = {}
        # NOTE: Sizes() settings cannot be overwritten by user
        if "keybindings" in data:
            args = parse_keybind_input(
                dict(filter(lambda x: x[0] != "numbers", data["keybindings"].items()))
            )
            if "numbers" in data["keybindings"]:
                args.update(
                    {"_numbers": parse_number_input(data["keybindings"]["numbers"])}
                )

            user_settings["keybinds"] = Keybinds(**args)
        if "colours" in data:
            args = parse_colours(
                dict(
                    filter(lambda x: x[0] != "hint-highlights", data["colours"].items())
                )
            )
            if "hint-highlights" in data["colours"]:
                args.update(
                    {
                        "_hint_highlight": parse_hint_highlight(
                            data["colours"]["hint-highlights"]
                        )
                    }
                )
            print(args)
            user_settings["colours"] = Colours(**args)
        if "gameplay" in data:
            user_settings["gameplay"] = Gameplay(**data["gameplay"])
        if "developer" in data:
            user_settings["developer"] = Developer(**data["developer"])

        return Settings(**user_settings)
    except Exception as e:
        # Catches missing settings keys, invalid settings keys and anything that fails the parsing funcs
        raise e from ValueError("Invalid settings file")


# Use user-defined settings or fallback to defaults
if SETTINGS.is_file():
    settings = load_settings(SETTINGS)
else:
    settings = load_settings()

# TODO: Don't let anyone import anything besides this
