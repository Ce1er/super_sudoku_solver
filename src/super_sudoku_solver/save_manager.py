#!/usr/bin/env python

from pathlib import Path
from typing import Any, Literal, Optional
from collections.abc import Callable
from super_sudoku_solver.paths import (
    PUZZLE_DATA_DIR,
    PUZZLE_DIR,
    PUZZLE_JSON,
    GUESSES_SUFFIX,
    CANDIDATES_SUFFIX,
    DEFAULT_PUZZLES,
    DEFAULT_CONFIG,
    SETTINGS,
    CACHE_DIR
)
import json
from jsonschema import ValidationError, validate
import numpy as np
import numpy.typing as npt
from uuid import uuid7, UUID
import re
from super_sudoku_solver.custom_types import Candidates, Cells
from functools import total_ordering, partial
import socket
from super_sudoku_solver.settings import settings
import sys
import os
import tempfile
from io import BufferedWriter
import logging
import shutil

DIFFICULTIES = ["easy", "medium", "hard"]
DIFFICULTIES_T = Literal["easy", "medium", "hard"]


def ensure_single_instance():
    """
    Ensure only one instance of app is running
    Returns:
        sock: socket that the app app binds to. This must not be garbage collected.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.bind(("127.0.0.1", settings.developer.port))
    except OSError:
        logging.error(
            f"Failed to launch. Another instance appears to be running.\
            If there is no other instance running it could be a result of another app running on port {settings.developer.port}."
        )
        sys.exit()

    return sock


# Prevents save files from being accessed by multiple processes
lock_socket = ensure_single_instance()

# TODO: work out how this should interact with sudoku.Board
# Right now I think that Board should get things from here


def atomic_write(
    data: bytes,
    dst: os.PathLike,
    save_func: Callable[[BufferedWriter, bytes], Any] = lambda file, data: file.write(
        data
    ),
):
    """
    Write binary data to a file atomically. This will prevent partially written files caused by kernel panics,
    power outages, etc. at the cost of some performance. Best used with important data that gets written
    infrequently and/or large data.
    Args:
        data: bytes data to save
        dst: path to save to
        save_func: optional custom write function which takes `dst` file in mode "wb" and `data` as input
    """
    # Avoid writing to file directly to avoid corruption
    # https://lwn.net/Articles/457667/
    # CACHE_DIR is not used here because it may be on a different filesystem.
    fd, tmp_path = tempfile.mkstemp(dir=dst.parent)

    try:
        with os.fdopen(fd, "wb") as f:
            print(type(f))
            save_func(f, data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, dst)

        dir = os.open(dst.parent, os.O_DIRECTORY)

        try:
            os.fsync(dir)
        finally:
            os.close(dir)

    except Exception:
        # If fail before os.replace tmp_file will persist
        Path(tmp_path).unlink(missing_ok=True)
        raise


@total_ordering
class Puzzle:
    def __init__(self, uuid: str, clues: str, difficulty: str, puzzle_data_dir: Path= PUZZLE_DATA_DIR):
        self.puzzle_data_dir = puzzle_data_dir
        self._guesses_file: Path = self.puzzle_data_dir / (uuid + GUESSES_SUFFIX)
        self._candidates_file: Path = self.puzzle_data_dir / (uuid + CANDIDATES_SUFFIX)
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

    # np_atomic_save = staticmethod(
    #     partial(atomic_write, save_func=lambda file, data: np.save(file, data))
    # )

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
        # I don't want to wait for an atomic save here because that extra time would be noticable to user
        # Corruption is very unlikely and would only affect one puzzle anyway
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

    # Could maybe use functools.singledispatchmethod instead but that may be less clear
    # Worth trying though
    @property
    def clues(self) -> Cells:
        if isinstance(self._clues, str):
            values = [-1 if clue == "." else int(clue) - 1 for clue in self._clues]
            self._clues: Cells = np.array(values, dtype=np.int8).reshape((9, 9))
            self._clues.flags.writeable = False

        return self._clues

    @property
    def cells(self) -> Cells:
        # TODO: check this works
        return np.where(self.clues != -1, self.clues, self.guesses)

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
        self._candidates_file.unlink(missing_ok=True)
        self._guesses_file.unlink(missing_ok=True)

        self._guesses = None
        self._candidates = None

    # To allow sorting
    # Maybe a sorting function is better than operator overloading?
    # Consider https://docs.python.org/3/howto/sorting.html#sortinghowto
    def __lt__(self, other) -> bool:
        if not isinstance(other, Puzzle):
            raise NotImplementedError

        # Sort first based on difficulty
        # Then on time of puzzle creation
        return (DIFFICULTIES.index(self._difficulty), self._uuid.time) < (
            DIFFICULTIES.index(other.difficulty),
            other.uuid.time,
        )

    # Other comparisons aren't strictly needed for sorting with python inbuild functions
    # But since lt is defined I would rather them all be (@total_ordering does the rest)
    def __eq__(self, other) -> bool:
        if not isinstance(other, Puzzle):
            raise NotImplementedError

        return self._difficulty == other.difficulty and np.array_equal(
            self._clues, other.clues
        )


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
                                "pattern": rf"^({'|'.join(DIFFICULTIES)})$",
                            },
                            "clues": {
                                "description": "The cells initially set",
                                "type": "string",
                                "pattern": r"^[1-9\.]{81}$",
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
        if self.puzzle_json.is_file():
            with self.puzzle_json.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            with self.puzzle_json.open("w", encoding="utf-8") as f:
                data = {"puzzles": {}}
                f.write(json.dumps(data))

        try:
            validate(data, self.SCHEMA)
        except ValidationError as e:
            raise e from ValueError("Invalid puzzles.json file")

        puzzles = {}
        for id, puzzle in data["puzzles"].items():
            puzzles[id] = Puzzle(
                id, puzzle["clues"], puzzle["difficulty"], self.puzzle_data_dir
            )

        # Sort puzzles based on Puzzle.__lt__
        puzzles = dict(sorted(puzzles.items(), key=lambda x: x[1]))
        self._puzzles = puzzles

    def __init__(self, puzzle_json: Path= PUZZLE_JSON, puzzle_data_dir: Path= PUZZLE_DATA_DIR):
        self.puzzle_json = puzzle_json
        self.puzzle_data_dir = puzzle_data_dir
        self.load()

    @property
    def puzzles(self):
        """
        Returns:
            dict mapping uuid to puzzle
        """
        return self._puzzles

    @property
    def puzzle_map(self) -> dict[str, Puzzle]:
        """
        Returns:
            dict that maps puzzle names to Puzzle objects
        """
        puzzle_map = {}
        last_difficulty = None
        n = 1
        # Can safely assume difficulty is non-decreasing
        for puzzle in self._puzzles.values():
            if puzzle.difficulty == last_difficulty:
                n += 1
            else:
                n = 1

            last_difficulty = puzzle.difficulty
            name = puzzle.difficulty + " " + str(n)
            puzzle_map[name] = puzzle

        return puzzle_map

    def save(self):
        """
        Save any changes to puzzles persistently
        """
        new = {"puzzles": {}}
        for puzzle in self._puzzles.values():
            new["puzzles"][str(puzzle.uuid)] = {
                "difficulty": puzzle.difficulty,
                "clues": puzzle.str_clues,
            }

        try:
            validate(new, self.SCHEMA)
        except ValidationError as e:
            raise e from ValueError("Failed to save")

        data = json.dumps(new).encode("utf-8")

        # data is not written very often and can be large if there are lots of puzzles saved
        # so safety from atomic_write is worth performance hit
        try:
            atomic_write(data, self.puzzle_json)
        except Exception as e:
            raise RuntimeError("Puzzle JSON save failed.") from e

    def add_puzzle(self, clues: str, difficulty: DIFFICULTIES_T):
        """
        Add a new puzzle.
        Does not save automatically. Use save() method after.
        Args:
            clues: initial state of the puzzle
            difficulty: approximate difficulty of puzzle
        """
        if not re.fullmatch(r"[1-9\.]{81}", clues):
            raise ValueError("Invalid clues")
        if difficulty not in DIFFICULTIES:
            raise ValueError("Invalid difficulty")

        uuid = uuid7()
        self._puzzles[str(uuid)] = Puzzle(
            str(uuid), clues, difficulty, self.puzzle_data_dir
        )

    def delete_puzzle(self, id):
        """
        Delete a puzzle.
        Does not save automatically. Use save() method after.
        Args:
            id: uuid of puzzle to delete
        """
        self._puzzles[id].reset()
        del self._puzzles[id]

    def update_puzzle_difficulty(self, id, difficulty: DIFFICULTIES_T):
        """
        Change a puzzle's difficulty.
        Does not save automatically. Use save() method after.
        Args:
            id: uuid of puzzle to update
            difficulty: new difficulty
        """
        self._puzzles[id].difficulty = difficulty
        # TODO: reloading should be unnecessary but need to test that


puzzles = Puzzles()


def confirm(prompt: str) -> bool:
    try:
        response = input(f"{prompt} (y/N) ")
    except Exception:
        return False
    return response.strip().lower() in ("y", "yes")


def main(args):
    if args.add:
        for clues, difficulty in args.add:
            puzzles.add_puzzle(clues, difficulty)

    if args.update:
        for id, difficulty in args.update:
            puzzles.update_puzzle_difficulty(id, difficulty)

    if args.delete:
        for puzzle in args.delete:
            puzzles.delete_puzzle(puzzle)

    if args.reset_puzzle_data:
        if not confirm(
            "Are you sure? This action will revert all puzzles to their original state and is irreversable."
        ):
            print("aborting")
            exit()
        for puzzle in puzzles.puzzles.values():
            puzzle.reset()

    if args.reset_all_data:
        if not confirm(
            "Are you sure? This action will delete all puzzles is irreversable."
        ):
            print("aborting")
            exit()

        uuids = list(puzzles.puzzles.keys())
        for puzzle in uuids:
            puzzles.delete_puzzle(puzzle)

    if args.restore_default_puzzles:
        # Puzzle data dir is not used but has to be set
        # It shouldn't be written to but if it is it will be cleared on next app launch anyway
        default_puzzles = Puzzles(DEFAULT_PUZZLES, CACHE_DIR)

        # Add all the default puzzles unless they are already saved
        for uuid, puzzle in default_puzzles.puzzles.items():
            if uuid not in puzzles.puzzles:
                puzzles.add_puzzle(puzzle.str_clues, puzzle.difficulty)

    if args.restore_default_config:
        shutil.copy(DEFAULT_CONFIG, SETTINGS)

    puzzles.save()
