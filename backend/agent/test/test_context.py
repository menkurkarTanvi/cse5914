from __future__ import annotations
import uuid
import asyncio
import uuid
from datetime import date
from typing import Literal, NotRequired, TypedDict
from agent.state import WorkoutAgentState
from agent.nodes.context import load_user_context

async def context():
    state = WorkoutAgentState = {'user_id': "851a30d8-f5e5-4f45-9425-041f131660f9"}
    content = await load_user_context(state)
    print("hi")
    print(content)

if __name__ == "__main__":
    asyncio.run(context())