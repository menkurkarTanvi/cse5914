import requests, time

BASE = "https://wger.de/api/v2"
exercises = []
url = f"{BASE}/exerciseinfo/?language=2&limit=100"

while url:
    r = requests.get(url, headers={"Accept": "application/json"})
    r.raise_for_status()
    data = r.json()
    exercises.extend(data["results"])
    url = data["next"]
    time.sleep(0.2)  # be polite, endpoint is unthrottled but don't hammer it

print(len(exercises), "exercises pulled")
