"""Step 1 of the tutorial's worked example: book_room before it learned to ask.

This is the deliberately wrong first version shown in unit 01, section 4. It compiles,
runs, and always books the first free room in sorted order, which is the bug the section
is about. Kept as a runnable file so the listing in the tutorial is copied from code that
was executed, not typed into prose.
"""

import asyncio

from mcp import Client
from mcp.server import MCPServer

mcp = MCPServer("Room Desk (step 1)")

ROOMS = {
    "aurora": {"seats": 4, "floor": 2},
    "basalt": {"seats": 8, "floor": 2},
    "cinder": {"seats": 8, "floor": 5},
}

BOOKED: set[tuple[str, str]] = {("basalt", "2026-08-03")}


def _free_rooms(date: str, attendees: int) -> list[str]:
    return sorted(
        name
        for name, room in ROOMS.items()
        if room["seats"] >= attendees and (name, date) not in BOOKED
    )


@mcp.tool()
def book_room(date: str, attendees: int) -> str:
    """Book a meeting room."""
    free = _free_rooms(date, attendees)
    BOOKED.add((free[0], date))
    return f"Booked {free[0]} on {date} for {attendees}."


async def main() -> None:
    async with Client(mcp) as client:
        result = await client.call_tool("book_room", {"date": "2026-08-12", "attendees": 6})
        print("book_room:", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
