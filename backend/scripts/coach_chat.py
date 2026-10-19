"""
Chat with the AI coach from the terminal, through the running backend.

Signs in as a demo user by minting a token, so no password is needed.
Run from the backend folder, with the backend running (fastapi dev main.py):

    python scripts/coach_chat.py --seed     # once: create the demo users and their plans
    python scripts/coach_chat.py            # chat as the gym demo user
    python scripts/coach_chat.py knee       # chat as the bodyweight user with a bad knee
    python scripts/coach_chat.py you@example.com   # chat as any account that has a profile
    python scripts/coach_chat.py --reset    # rebuild the demo users' plans from scratch

Changes you confirm in the chat are written to that user's workout in your
local database. Use --reset to undo them.
"""

import asyncio
import logging
import sys
import uuid
from pathlib import Path

import httpx

# Lets the script import the backend packages from any folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, func, select  # noqa: E402

API_URL = "http://localhost:8000/coach/chat"

DEMO_USERS = {
    "gym": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000901"),
        "email": "e2e-gym@fitstack.local",
        "profile": {
            "goal": "hypertrophy",
            "experience_level": "intermediate",
            "available_equipment": ["Full gym"],
            "preferred_exercises": ["bench press"],
            "disliked_exercises": [],
            "limitations": [],
        },
        "availability": {"Monday": 60, "Tuesday": 60, "Thursday": 45, "Friday": 60},
    },
    "knee": {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000902"),
        "email": "e2e-bodyweight@fitstack.local",
        "profile": {
            "goal": "general_fitness",
            "experience_level": "beginner",
            "available_equipment": ["Bodyweight"],
            "preferred_exercises": [],
            "disliked_exercises": ["burpee"],
            "limitations": ["bad left knee"],
        },
        "availability": {"Tuesday": 30, "Saturday": 30},
    },
}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ============================================================
# Demo users
# ============================================================

async def seed(reset: bool) -> None:
    """Create any missing demo users, then give each a 4-week plan using the
    new-program path of the workout agent. With reset, delete their plans first."""
    from database.database import AsyncSessionLocal
    from models.exercise import Exercise
    from models.profile import Profile
    from models.user import User
    from models.user_availability import UserAvailability
    from models.workout_program import WorkoutProgram

    async with AsyncSessionLocal() as session:
        if not await session.scalar(select(func.count(Exercise.exercise_id))):
            sys.exit("The exercises table is empty. Load the exercise catalog first (see README).")

        for key, demo in DEMO_USERS.items():
            if await session.get(User, demo["id"]) is None:
                session.add(User(id=demo["id"], email=demo["email"], hashed_password="not-for-login"))
                await session.flush()
                session.add(Profile(user_id=demo["id"], **demo["profile"]))
                session.add_all(
                    UserAvailability(
                        user_id=demo["id"],
                        day_of_week=day,
                        is_available=day in demo["availability"],
                        max_duration_minutes=demo["availability"].get(day),
                    )
                    for day in DAYS
                )
                print(f"Created demo user {key} ({demo['email']})")
            if reset:
                # Plans, workouts and planned exercises go with it (ON DELETE CASCADE).
                await session.execute(delete(WorkoutProgram).where(WorkoutProgram.user_id == demo["id"]))
        await session.commit()

    for key, demo in DEMO_USERS.items():
        state = await _generate_program(demo["id"])
        if state is None:
            print(f"{key}: already has an active plan (use --reset to rebuild it)")
        else:
            upcoming = state["upcoming_workout"]
            print(f"{key}: new 4-week plan, first workout {upcoming['day_of_week'].title()} {upcoming['scheduled_date']}")


async def _generate_program(user_id: uuid.UUID) -> dict | None:
    """Run the new-program path for one user, or None if they have a plan."""
    from agent.nodes.context import load_user_context
    from agent.nodes.new_program import (
        analyze_starting_point, generate_4_week_program, retrieve_candidate_exercises,
        save_program, validate_program,
    )

    state = {"user_id": user_id}
    state.update(await load_user_context(state))
    if state.get("active_program") is not None:
        return None
    for step in (analyze_starting_point, retrieve_candidate_exercises, generate_4_week_program,
                 validate_program, save_program):
        state.update(await step(state))
    return state


async def _find_user_id(name: str) -> str:
    if name in DEMO_USERS:
        return str(DEMO_USERS[name]["id"])

    from database.database import AsyncSessionLocal
    from models.user import User

    async with AsyncSessionLocal() as session:
        user = await session.scalar(select(User).where(User.email == name))
    if user is None:
        sys.exit(f"No user {name!r}. Use gym, knee, or an account's email (run --seed for the demo users).")
    return str(user.id)


# ============================================================
# Chat loop
# ============================================================

def chat(user_name: str) -> None:
    from core.auth import create_access_token

    user_id = asyncio.run(_find_user_id(user_name))
    history: list[dict] = []
    pending_action = None

    print(f"Chatting as {user_name}. Type 'quit' to stop, 'reset' to start a new conversation.\n")
    while True:
        try:
            message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not message:
            continue
        if message == "quit":
            break
        if message == "reset":
            history, pending_action = [], None
            print("(conversation cleared)\n")
            continue

        # Login tokens expire after 15 minutes, so make a fresh one each turn.
        token = asyncio.run(create_access_token({"sub": user_id}))
        try:
            response = httpx.post(
                API_URL,
                json={"message": message, "history": history, "pending_action": pending_action},
                headers={"Authorization": f"Bearer {token}"},
                timeout=60,
            )
        except httpx.ConnectError:
            print("Can't reach the backend. Start it in another terminal: fastapi dev main.py\n")
            continue
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.json().get('detail', response.text)}\n")
            continue

        data = response.json()
        print(f"coach> {data['reply']}")
        notes = [f"intent: {data['intent']}"]
        if data["needs_follow_up"]:
            notes.append("waiting for your answer")
        if data["plan_changed"]:
            notes.append("WORKOUT UPDATED")
        print(f"       ({', '.join(notes)})\n")

        history += [
            {"role": "user", "content": message},
            {"role": "assistant", "content": data["reply"]},
        ]
        pending_action = data["pending_action"]


def main() -> None:
    # The database engine logs every SQL statement; keep the chat readable.
    logging.disable(logging.CRITICAL)
    import database.database
    database.database.engine.echo = False

    args = sys.argv[1:]
    if args and args[0] in ("--seed", "--reset"):
        asyncio.run(seed(reset=args[0] == "--reset"))
        return
    chat(args[0] if args else "gym")


if __name__ == "__main__":
    main()
