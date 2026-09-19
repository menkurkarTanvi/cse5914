#File to handle exercise ingestion from Kinetic API
import requests, time, json

exercises = []
url = f"https://api.kinetic.place/v1/exercises"

r = requests.get(url, headers={"Accept": "application/json"})
r.raise_for_status()
data = r.json()


print(data['data'][1])
