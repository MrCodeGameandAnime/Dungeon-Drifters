import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "app"
sys.path.insert(0, str(APP_DIR))

from main_loop import main  # noqa: E402


if __name__ == "__main__":
    main()
