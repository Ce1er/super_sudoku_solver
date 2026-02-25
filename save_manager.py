from pathlib import Path
from typing import Optional
from paths import PUZZLE_DATA, PUZZLE_DIR
import json
from jsonschema import ValidationError, validate
import numpy as np
from uuid import uuid7, UUID
import re
from custom_types import Candidates, Cells

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

        # PERF: lazy load numpy arrays
        self._clues: str | Cells = clues
        self._guesses: Optional[Cells] = None
        self._candidates: Optional[Candidates] = None

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
        "type": "object",
        "properties": {
            "puzzles": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        # TODO: make puzzles an object with uuid as the key
                        "uuid": {
                            "type": "string",
                            "pattern": r"^[0-9a-f]{8}(?:\-[0-9a-f]{4}){3}-[0-9a-f]{12}$",
                        },
                        "difficulty": {
                            "type": "string",
                            "pattern": rf"^({"|".join(DIFFICULTIES)})$",
                        },
                        "clues": {"type": "string", "pattern": r"^[1-9\.]{81}$"},
                    },
                    "required": ["clues", "difficulty", "uuid"],
                },
            }
        },
        "required": ["puzzles"],
    }

    def __init__(self):
        with PUZZLE_DATA.open("r", encoding="utf-8") as f:
            self._json = json.load(f)
        try:
            validate(self._json, self.SCHEMA)
        except ValidationError as e:
            raise e from ValueError("Invalid puzzles.json file")

        puzzles = []
        for puzzle in self._json["puzzles"]:
            puzzles.append(
                Puzzle(puzzle["uuid"], puzzle["clues"], puzzle["difficulty"])
            )
        puzzles.sort()

        puzzle_map = {}
        last_difficulty = None
        n = 1
        for puzzle in puzzles:
            if puzzle["difficulty"] == last_difficulty:
                n += 1
            else:
                n = 1

            last_difficulty = puzzle["difficulty"]
            name = puzzle["difficulty"] + "_" + str(n)
            puzzle_map[name] = puzzle

        self._puzzles = puzzle_map

    @property
    def puzzles(self):
        return self._puzzles

    def get_puzzles(self):
        for puzzle in self._puzzles:
            yield puzzle

    def save(self):
        data = json.dumps(self._json)
        with PUZZLE_DATA.open("w", encoding="utf-8") as f:
            f.write(data)

    def add_puzzle(self, clues, difficulty):
        if not re.fullmatch(r"[1-9\.]{81}", clues):
            raise ValueError("Invalid clues")
        if difficulty not in DIFFICULTIES:
            raise ValueError("Invalid difficulty")

        uuid = uuid7()
        self._json["puzzles"].append(
            {"uuid": str(uuid), "difficulty": difficulty, "clues": clues}
        )
        self.save()


if __name__ == "__main__":
    p = Puzzles()
    print(p._json)
    for x in p.get_puzzles():
        print(x.uuid, x.clues)
