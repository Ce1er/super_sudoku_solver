from pathlib import Path
from appdirs import user_data_dir, user_config_dir

APP_NAME = "super_sudoku_solver"
APP_AUTHOR = "matilda"  # Only used by Windows

SRC_DIR = Path(__file__).resolve().parent
PUZZLE_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))
PUZZLE_JSON = PUZZLE_DIR / "puzzles.json"
PUZZLE_DATA = PUZZLE_DIR / ".data"
GUESSES_SUFFIX = "_guesses.npy"
CANDIDATES_SUFFIX = "_candidates.npy"
CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))
SETTINGS = CONFIG_DIR / "settings.toml"

if not PUZZLE_DATA.exists():
    PUZZLE_DATA.mkdir(parents=True)

if not CONFIG_DIR.exists():
    SETTINGS.parent.mkdir(parents=True)
