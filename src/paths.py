"""
Module defining file and directory locations based on 
"""
from pathlib import Path
from appdirs import user_data_dir, user_config_dir

APP_NAME = "super-sudoku-solver"

SRC_DIR = Path(__file__).resolve().parent
PUZZLE_DIR = Path(user_data_dir(APP_NAME))
PUZZLE_JSON = PUZZLE_DIR / "puzzles.json"
PUZZLE_DATA_DIR = PUZZLE_DIR / ".data"
GUESSES_SUFFIX = "_guesses.npy"
CANDIDATES_SUFFIX = "_candidates.npy"
CONFIG_DIR = Path(user_config_dir(APP_NAME))
SETTINGS = CONFIG_DIR / "settings.toml"

if not PUZZLE_DATA_DIR.exists():
    PUZZLE_DATA_DIR.mkdir(parents=True)

if not CONFIG_DIR.exists():
    SETTINGS.parent.mkdir(parents=True)
