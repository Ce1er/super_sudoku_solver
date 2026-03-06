from pathlib import Path
from typing import Optional
from paths import PUZZLE_DATA, PUZZLE_DIR
import json
from jsonschema import ValidationError, validate
import numpy as np
from uuid import uuid7, UUID
import re
from custom_types import Candidates, Cells
import argparse

GUESSES_SUFFIX = "_guesses"
CANDIDATES_SUFFIX = "_candidates"
DIFFICULTIES = ["easy", "medium", "hard"]


# TODO: work out how this should interact with sudoku.Board
# Right now I think that Board should get things from here
class Puzzle:
    def __init__(self, uuid: str, clues: str, difficulty: str):
        self._guesses_file: Path = PUZZLE_DIR / (uuid + "_guesses")
        self._candidates_file: Path = PUZZLE_DIR / (uuid + "_candidates")
        self._uuid: UUID = UUID(uuid)  # (uuid7)
        self._difficulty: str = difficulty

        # In case Puzzle needs to be saved back to json
        self._str_clues = clues

        # PERF: lazy load numpy arrays
        self._clues: str | Cells = clues
        self._guesses: Optional[Cells] = None
        self._candidates: Optional[Candidates] = None

    @property
    def str_clues(self) -> str:
        return self._str_clues

    @property
    def guesses(self) -> Cells:
        if self._guesses is not None:
            return self._guesses

        # Default if there is no save data
        if not self._guesses_file.is_file():
            return np.full((9, 9), -1, dtype=np.int8)

        return np.load(self._guesses_file)

    @guesses.setter
    def guesses(self, new: Cells) -> None:
        # TODO: consider using a copy instead.
        # If not warn against mutating array
        self._guesses = new
        # I don't mind waiting for IO here because
        np.save(self._guesses_file, new)

    @property
    def candidates(self) -> Candidates:
        if self._candidates is not None:
            return self._candidates

        if not self._candidates_file.is_file():
            return np.full((9, 9, 9), False, dtype=np.int8)

        return np.load(self._candidates_file)

    @candidates.setter
    def candidates(self, new: Candidates) -> None:
        self._candidates = new
        np.save(self._candidates_file, new)

    @property
    def clues(self) -> Cells:
        if isinstance(self._clues, str):
            values = [-1 if clue == "." else int(clue) - 1 for clue in self._clues]
            self._clues: Cells = np.array(values, dtype=np.int8).reshape((9, 9))
            self._clues.flags.writeable = False

        return self._clues

    @property
    def difficulty(self) -> str:
        return self._difficulty

    @difficulty.setter
    def difficulty(self, new: str) -> None:
        if new in DIFFICULTIES:
            self._difficulty = new
        else:
            raise ValueError("Invalid difficulty")

    @property
    def uuid(self) -> UUID:
        return self._uuid

    def reset(self) -> None:
        # Delete save files
        self._candidates_file.unlink()
        self._guesses_file.unlink()

    # To allow sorting
    def __lt__(self, other: "Puzzle") -> bool:
        # Sort first based on difficulty
        if DIFFICULTIES.index(self._difficulty) < DIFFICULTIES.index(other.difficulty):
            return True

        # Then on time of puzzle creation
        return self._uuid.time < other.uuid.time


class Puzzles:
    SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Puzzles",
        "description": "The initial state of multiple puzzles",
        "type": "object",
        "properties": {
            "puzzles": {
                "type": "object",
                "patternProperties": {
                    r"^[0-9a-f]{8}(?:\-[0-9a-f]{4}){3}-[0-9a-f]{12}$": {
                        "type": "object",
                        "properties": {
                            "difficulty": {
                                "description": "The approximate difficulty of the puzzle",
                                "type": "string",
                                "pattern": rf"^({"|".join(DIFFICULTIES)})$",
                            },
                            "clues": {
                                "description": "The cells initially set",
                                "type": "string",
                                "pattern": r"^[1-9\.]{81}",
                            },
                        },
                        "additionalProperties": False,
                        "required": ["difficulty", "clues"],
                    }
                },
                "additionalProperties": False,
            }
        },
        "additionalProperties": False,
        "required": ["puzzles"],
    }

    def load(self):
        if PUZZLE_DATA.is_file():
            with PUZZLE_DATA.open("r", encoding="utf-8") as f:
                self._json = json.load(f)
        else:
            with PUZZLE_DATA.open("w", encoding="utf-8") as f:
                f.write(json.dumps({"puzzles": {}}))

        print("j: ", self._json)

        try:
            validate(self._json, self.SCHEMA)
        except ValidationError as e:
            raise e from ValueError("Invalid puzzles.json file")

        puzzles = {}
        for id, puzzle in self._json["puzzles"].items():
            puzzles[id] = Puzzle(id, puzzle["clues"], puzzle["difficulty"])

        # Sort puzzles based on difficulty and time created
        puzzles = dict(sorted(puzzles.items(), key=lambda x: x[1]))
        self._puzzles = puzzles
        print(f"asdf {self._json}\n{self._puzzles}")

    def __init__(self):
        self.load()

    @property
    def puzzle_map(self):
        puzzle_map = {}
        last_difficulty = None
        n = 1
        for puzzle in self._puzzles:
            if puzzle["difficulty"] == last_difficulty:
                n += 1
            else:
                n = 1

            last_difficulty = puzzle.difficulty
            name = puzzle.difficulty + "_" + str(n)
            puzzle_map[name] = puzzle

        return puzzle_map

    def save(self):
        # data = json.dumps(self._json)

        new = {"puzzles": {}}
        print(self._puzzles)
        for puzzle in self._puzzles.values():
            new["puzzles"][str(puzzle.uuid)] = {
                "difficulty": puzzle.difficulty,
                "clues": puzzle.str_clues,
            }

        try:
            validate(new, self.SCHEMA)
        except ValidationError as e:
            raise e from ValueError("Failed to save")

        data = json.dumps(new)
        with PUZZLE_DATA.open("w", encoding="utf-8") as f:
            f.write(data)

    def add_puzzle(self, clues, difficulty):
        if not re.fullmatch(r"[1-9\.]{81}", clues):
            raise ValueError("Invalid clues")
        if difficulty not in DIFFICULTIES:
            raise ValueError("Invalid difficulty")

        uuid = uuid7()
        self._puzzles[str(uuid)] = Puzzle(str(uuid), clues, difficulty)

        self.save()
        self.load()

    def delete_puzzle(self, id):
        print("p", self._puzzles)
        print("q", self._json)
        del self._puzzles[id]
        self.save()
        self.load()

    def update_puzzle_difficulty(self, id, difficulty):
        print("i: ", self._puzzles)
        self._puzzles[id].difficulty = difficulty
        self.save()
        self.load()


if __name__ == "__main__":
    puzzles = Puzzles()
    parser = argparse.ArgumentParser(
        prog="save_manager", description="Create, delete or modify saved puzzles."
    )
    parser.add_argument(
        "-d",
        "--delete",
        nargs=1,
        action="append",
        metavar=("UUID"),
        help="Delete a puzzle",
    )
    parser.add_argument(
        "-u",
        "--update",
        nargs=2,
        action="append",
        metavar=("UUID", "DIFFICULTY"),
        help="Change a puzzle's difficulty",
    )
    parser.add_argument(
        "-a",
        "--add",
        nargs=2,
        action="append",
        metavar=("CLUES", "DIFFICULTY"),
        help="Add a puzzle",
    )

    args = parser.parse_args()

    if args.add:
        for clues, difficulty in args.add:
            puzzles.add_puzzle(clues, difficulty)

    if args.update:
        for id, difficulty in args.update:
            puzzles.update_puzzle_difficulty(id, difficulty)

    if args.delete:
        for id in args.delete:
            puzzles.delete_puzzle(id[0])

# TODO: stuff to stop this being ran if main program is being ran
