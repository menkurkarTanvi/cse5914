# Client for the Kinetic exercise API (https://api.kinetic.place)
import httpx

BASE_URL = "https://api.kinetic.place/v1"


def fetch_exercises_page(page: int = 1, limit: int = 100) -> dict:
    response = httpx.get(f"{BASE_URL}/exercises", params={"page": page, "limit": limit}, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_all_exercises(limit: int = 100) -> list[dict]:
    exercises = []
    page = 1
    while True:
        payload = fetch_exercises_page(page=page, limit=limit)
        exercises.extend(payload["data"])
        if len(exercises) >= payload["total"]:
            break
        page += 1
    return exercises


def fetch_exercise(exercise_id: str) -> dict:
    response = httpx.get(f"{BASE_URL}/exercises/{exercise_id}", timeout=10)
    response.raise_for_status()
    return response.json()
