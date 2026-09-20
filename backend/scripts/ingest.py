# Pull the full exercise catalog from the Kinetic API and cache it locally
import json
from pathlib import Path

from kinetic_client import fetch_all_exercises

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "kinetic_exercises.json"


def main() -> None:
    exercises = fetch_all_exercises()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(exercises, indent=2))
    print(f"Fetched {len(exercises)} exercises -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
