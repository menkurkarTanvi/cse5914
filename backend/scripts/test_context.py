"""Manually smoke-test the workout agent's context loader."""

import argparse
import asyncio
import json
import uuid

from agent.nodes.context import load_user_context


async def main(user_id: uuid.UUID) -> None:
    context = await load_user_context({"user_id": user_id})
    print(json.dumps(context, indent=2, default=str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("user_id", type=uuid.UUID, help="Existing users.id value")
    args = parser.parse_args()
    asyncio.run(main(args.user_id))
