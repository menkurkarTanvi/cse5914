def test_create_and_get_profile(client):
    response = client.post(
        "/api/v1/profiles",
        json={
            "display_name": "Taylor",
            "goal": "strength",
            "experience_level": "beginner",
            "equipment": ["Dumbbells", "bench"],
            "availability": [{"day_of_week": 0, "session_minutes": 45}],
            "limitations": [{"body_area": "knee", "notes": "No jumping", "hard_exclusion": True}],
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["training_block_weeks"] == 4
    assert created["equipment"] == [{"name": "dumbbells"}, {"name": "bench"}]

    fetched = client.get(f'/api/v1/profiles/{created["id"]}')
    assert fetched.status_code == 200
    assert fetched.json()["limitations"][0]["hard_exclusion"] is True


def test_rejects_duplicate_availability_days(client):
    response = client.post(
        "/api/v1/profiles",
        json={
            "display_name": "Taylor",
            "goal": "endurance",
            "experience_level": "intermediate",
            "availability": [
                {"day_of_week": 1, "session_minutes": 30},
                {"day_of_week": 1, "session_minutes": 60},
            ],
        },
    )
    assert response.status_code == 422
