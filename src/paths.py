"""
Module defining file and directory locations based on operating system's conventions
"""

from pathlib import Path
from appdirs import user_data_dir, user_config_dir, site_data_dir, user_log_dir, site_config_dir
import shutil

APP_NAME = "super-sudoku-solver"

SRC_DIR = Path(__file__).resolve().parent

PUZZLE_DIR = Path(user_data_dir(APP_NAME))
PUZZLE_JSON = PUZZLE_DIR / "puzzles.json"
PUZZLE_DATA_DIR = PUZZLE_DIR / ".data"
GUESSES_SUFFIX = "_guesses.npy"
CANDIDATES_SUFFIX = "_candidates.npy"

_SETTINGS_FILE = "settings.toml"

CONFIG_DIR = Path(user_config_dir(APP_NAME))
SETTINGS = CONFIG_DIR / _SETTINGS_FILE

# These won't actually override settings so doesn't make sense to be in $XDG_CONFIG_DIRS
DEFAULT_DIR = Path(site_data_dir(APP_NAME))
DEFAULT_SETTINGS = DEFAULT_DIR / _SETTINGS_FILE

LOG_DIR = Path(user_log_dir(APP_NAME))

for dir in (PUZZLE_DATA_DIR, CONFIG_DIR, DEFAULT_DIR, LOG_DIR):
    dir.mkdir(parents=True, exist_ok=True)

# # A missing settings file isn't an issue but it would be easier for a user to edit from a skeleton
# if not SETTINGS.is_file() and DEFAULT_SETTINGS.is_file():
#     shutil.copyfile(_SETTINGS_FILE, SETTINGS)
