"""
Module defining file and directory locations based on operating system's conventions
"""

from pathlib import Path
from appdirs import user_data_dir, user_config_dir, site_data_dir, user_log_dir, site_config_dir, user_cache_dir
import shutil

APP_NAME = "super-sudoku-solver"

_SETTINGS_NAME = "settings.toml"
_PUZZLES_NAME = "puzzles.json"

# For any temporary files that need to be written
CACHE_DIR = Path(user_cache_dir(APP_NAME))

SRC_DIR = Path(__file__).resolve().parent
DEFAULT_PUZZLES = SRC_DIR / _PUZZLES_NAME
DEFAULT_CONFIG = SRC_DIR / _SETTINGS_NAME

PUZZLE_DIR = Path(user_data_dir(APP_NAME))
PUZZLE_JSON = PUZZLE_DIR / _PUZZLES_NAME
PUZZLE_DATA_DIR = PUZZLE_DIR / ".data"
GUESSES_SUFFIX = "_guesses.npy"
CANDIDATES_SUFFIX = "_candidates.npy"


CONFIG_DIR = Path(user_config_dir(APP_NAME))
SETTINGS = CONFIG_DIR / _SETTINGS_NAME

LOG_DIR = Path(user_log_dir(APP_NAME))

# TODO: this will mess with permissions
for dir in (PUZZLE_DATA_DIR, CACHE_DIR): #CONFIG_DIR, DEFAULT_DIR, LOG_DIR):
    dir.mkdir(parents=True, exist_ok=True)

# rm -rf ${CACHE_DIR}/*
for item in CACHE_DIR.iterdir():
    if item.is_dir():
        shutil.rmtree(item)
    else:
        item.unlink()


# # A missing settings file isn't an issue but it would be easier for a user to edit from a skeleton
# if not SETTINGS.is_file() and DEFAULT_SETTINGS.is_file():
#     shutil.copyfile(_SETTINGS_FILE, SETTINGS)
