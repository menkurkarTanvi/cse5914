# Week 3 API Contracts

Proposed request/response shapes for the week 3 backend APIs, so backend and
frontend can build against the same contract.

Conventions (matching the existing code):

- Routes live under the existing `/workouts` and `/profiles` routers.
- The user always comes from the JWT (`CurrentUserId`), never from the request body.
- JSON fields are snake_case, like the Pydantic schemas.
- Days are capitalized (`"Monday"`), like `schemas/profile.py`.

| # | API | Endpoint(s) | Status |
|---|-----|-------------|--------|
| 0 | Get the current plan | `GET /workouts/workoutPlan` | Route stub exists, needs implementing |
| 1 | Exercise swap | `GET .../alternatives`, `POST .../swap` | New |
| 2 | Workout completion, logging, feedback | `POST /workouts/{workout_id}/complete`, `POST /workouts/{workout_id}/skip` | New |
| 3 | Profile availability | `POST /profiles/createProfile`, `PUT /profiles/availability` | Create schema exists; update route is new |

---

## 0. Get the current plan

Needed first: the swap and logging APIs use the IDs it returns.

`GET /workouts/workoutPlan`. If the user has no active program, this runs the
workout agent first (new program path), then returns the result.

```json
{
  "program": {
    "program_id": "uuid",
    "goal": "hypertrophy",
    "start_date": "2026-10-12",
    "end_date": "2026-11-08",
    "status": "active",
    "current_week": 1
  },
  "workouts": [
    {
      "workout_id": "uuid",
      "week_number": 1,
      "day_of_week": "Monday",
      "scheduled_date": "2026-10-12",
      "status": "scheduled",
      "exercises": [
        {
          "workout_plan_exercise_id": "uuid",
          "exercise_id": "barbell-bench-press",
          "name": "Barbell Bench Press",
          "exercise_order": 1,
          "sets_planned": 3,
          "reps_min": 6,
          "reps_max": 12,
          "target_rpe_min": 7.0,
          "target_rpe_max": 8.0,
          "rest_seconds": 120,
          "planned_weight": 135.0,
          "weight_unit": "lb",
          "notes": "Chosen for the horizontal push slot: compound exercise for Chest."
        }
      ]
    }
  ]
}
```

Notes:

- The frontend's current `{ name, sets: "3 × 8–10" }` display can be built from
  `sets_planned`, `reps_min` and `reps_max`.
- `notes` explains why the exercise was picked (the explainability feature).
- `planned_weight` is `null` when there is no history for that exercise yet.

---

## 1. Exercise swap

### Get alternatives

`GET /workouts/exercises/{workout_plan_exercise_id}/alternatives?limit=5`

```json
{
  "current": {
    "exercise_id": "barbell-bench-press",
    "name": "Barbell Bench Press"
  },
  "alternatives": [
    {
      "exercise_id": "dumbbell-bench-press",
      "name": "Dumbbell Bench Press",
      "primary_muscles": ["Chest"],
      "equipment_required": ["Dumbbell"],
      "reason": "Same movement (horizontal push), uses equipment you have."
    }
  ]
}
```

### Apply a swap

`POST /workouts/exercises/{workout_plan_exercise_id}/swap`

Request:

```json
{
  "exercise_id": "dumbbell-bench-press",
  "apply_to": "this_workout"
}
```

`apply_to` is `"this_workout"` or `"rest_of_program"`.

Response: the updated planned exercise, same shape as an item in
`workouts[].exercises` in section 0.

Notes:

- Alternatives must pass the same hard filters as program generation
  (equipment, injuries, dislikes, difficulty). Rank them by matching
  `substitution_group` or movement family and primary muscle.
  `is_exercise_allowed` and `slot_score` in `agent/nodes/new_program.py` can be
  reused.
- A swap keeps the sets, reps and rest. `planned_weight` resets to `null`,
  because a weight doesn't carry over between exercises.
- Errors:
  - `404` if the planned exercise doesn't belong to this user.
  - `400` if `exercise_id` isn't an allowed alternative, so a client can't
    bypass the injury filter.

---

## 2. Workout completion, logging and feedback

Flow from the planning doc: mark the workout complete or incomplete. If it is
complete, log the sets, reps and weight, then give feedback.

Completion, logging and feedback go in **one request**, so a workout can't end
up marked complete with no sets logged.

### Complete a workout

`POST /workouts/{workout_id}/complete`

Request:

```json
{
  "exercises": [
    {
      "workout_plan_exercise_id": "uuid",
      "sets": [
        { "set_number": 1, "reps": 10, "weight": 135.0, "weight_unit": "lb", "rpe": 7.0 },
        { "set_number": 2, "reps": 9, "weight": 135.0, "weight_unit": "lb", "rpe": 8.0 }
      ]
    }
  ],
  "feedback": {
    "difficulty": "too_hard",
    "overall_rating": 4,
    "comments": "Shoulder felt tight on presses",
    "exercise_feedback": {
      "<workout_plan_exercise_id>": { "liked": false, "difficulty": "too_hard" }
    }
  }
}
```

- `difficulty` is `"too_easy"`, `"great"` or `"too_hard"`, matching the
  feedback buttons.
- `overall_rating` (1–5), `comments` and `exercise_feedback` are optional.
- `weight` is `null` for bodyweight exercises. `rpe` is optional.

Response:

```json
{
  "workout_id": "uuid",
  "status": "completed",
  "sets_logged": 9,
  "next_workout": {
    "workout_id": "uuid",
    "day_of_week": "Tuesday",
    "scheduled_date": "2026-10-13"
  }
}
```

### Mark a workout incomplete

`POST /workouts/{workout_id}/skip`

Optional request: `{ "reason": "sick" }`. Sets the workout's `status` to
`"skipped"`. The model has no "incomplete" status, so `skipped` stands in for it.

Notes:

- Storage:
  - Each set becomes a `WorkoutSet` row.
  - The feedback becomes one `WorkoutFeedback` row. `workout_id` is unique
    there, so posting feedback twice for the same workout returns `409`
    (or overwrites the first; decide one).
  - The workout's status becomes `"completed"`.
- Validation mirrors the database's constraints: `reps > 0`, `weight` is
  `null` or `>= 0`, and `rpe` is between 0 and 10.
- **Open decision:** `WorkoutFeedback` has no `difficulty` column. Either add a
  nullable column (one migration), or store it inside the `exercise_feedback`
  JSON. Recommended: a column, since the progression logic will query it.
- This is the data the current-program path reads
  (`load_recent_performance` → `analyze_progression`).

---

## 3. Profile availability

### Create profile (schema already defined)

`POST /profiles/createProfile`. The request schema already exists
(`CreateProfileRequest` in `schemas/profile.py`); the route just needs to save
it.

```json
{
  "profile": {
    "goal": "hypertrophy",
    "experience_level": "intermediate",
    "available_equipment": ["Full gym"],
    "preferred_exercises": [],
    "disliked_exercises": [],
    "limitations": ["bad left knee"]
  },
  "availability": [
    { "day_of_week": "Monday", "is_available": true, "max_duration_minutes": 30 },
    { "day_of_week": "Tuesday", "is_available": true, "max_duration_minutes": 15 },
    { "day_of_week": "Wednesday", "is_available": false, "max_duration_minutes": null }
  ]
}
```

### Update availability

`PUT /profiles/availability`. This replaces all of the user's availability
days.

Request:

```json
{
  "availability": [
    { "day_of_week": "Monday", "is_available": true, "max_duration_minutes": 30 },
    { "day_of_week": "Tuesday", "is_available": true, "max_duration_minutes": 15 }
  ]
}
```

Response: same shape as the existing `GET /profiles/profile`
(`{ "profile": {...}, "availability": [...] }`).

Notes:

- Reuse `AvailabilityRequest` and its validators:
  - each day appears at most once;
  - at least one day is available;
  - `max_duration_minutes` is 1–300.
- A profile or availability change should set `profile_changed`, so the agent
  re-checks the current plan (the compatibility branch in `agent/agent.txt`).

---

## Decisions for the team

1. Feedback `difficulty`: a new column, or stored in the JSON?
2. Swap scope: only `this_workout` for now, or `rest_of_program` too?
3. Path style: the existing routes mix camelCase (`/workoutPlan`,
   `/createProfile`). Keep that, or use the REST-style paths above?
