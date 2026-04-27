"""
Module defining file and directory locations based on operating system's conventions
"""

from platformdirs import user_data_path, user_config_path, user_runtime_path
from pathlib import Path
import shutil

APP_NAME = "super-sudoku-solver"

_SETTINGS_NAME = "settings.toml"
_PUZZLES_NAME = "puzzles.json"

# For any temporary files that need to be written
RUNTIME_DIR = user_runtime_path(APP_NAME)

SRC_DIR = Path(__file__).resolve().parent
DEFAULT_PUZZLES = SRC_DIR / _PUZZLES_NAME
DEFAULT_CONFIG = SRC_DIR / _SETTINGS_NAME

DATA_DIR = user_data_path(APP_NAME,  ensure_exists=True)
PUZZLE_JSON = DATA_DIR / _PUZZLES_NAME
PUZZLE_DATA_DIR = DATA_DIR / ".data"
GUESSES_SUFFIX = "_guesses.npy"
CANDIDATES_SUFFIX = "_candidates.npy"


CONFIG_DIR = user_config_path(APP_NAME, ensure_exists=True)
SETTINGS = CONFIG_DIR / _SETTINGS_NAME

for dir in (PUZZLE_DATA_DIR, RUNTIME_DIR, CONFIG_DIR):
    dir.mkdir(parents=True, exist_ok=True)

# rm -rf ${RUNTIME_DIR}/*
for item in RUNTIME_DIR.iterdir():
    if item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()
