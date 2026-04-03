from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PUZZLE_DIR = BASE_DIR / "puzzles"
PUZZLE_JSON = PUZZLE_DIR / "puzzles.json"
PUZZLE_DATA = PUZZLE_DIR / ".data"
GUESSES_SUFFIX = "_guesses.npy"
CANDIDATES_SUFFIX = "_candidates.npy"
SETTINGS = BASE_DIR / "settings.toml"

if not PUZZLE_DATA.exists():
    PUZZLE_DATA.mkdir(parents=True)
