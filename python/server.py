"""Room Desk: reference implementation for the MCP 2026-07-28 tutorial (Python)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from mcp.server import MCPServer
from mcp.server.mcpserver import AcceptedElicitation, Elicit, ElicitationResult, Resolve

mcp = MCPServer(
    "Room Desk",
    instructions="Check which meeting rooms are free before booking one.",
)

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
def check_availability(date: str, attendees: int) -> str:
    """List the meeting rooms free on a date that seat this many people."""
    free = _free_rooms(date, attendees)
    if not free:
        return f"No room on {date} seats {attendees}."
    return f"Free on {date} for {attendees}: {', '.join(free)}."


class RoomChoice(BaseModel):
    room: Literal["aurora", "basalt", "cinder"] = Field(description="Which room to book")


async def pick_room(date: str, attendees: int) -> RoomChoice | Elicit[RoomChoice]:
    """Resolver: decide the room, asking the user only when the choice is real."""
    free = _free_rooms(date, attendees)
    if not free:
        raise ValueError(f"No room on {date} seats {attendees}.")
    if len(free) == 1:
        return RoomChoice(room=free[0])  # type: ignore[arg-type]
    return Elicit(f"Rooms free on {date}: {', '.join(free)}. Which one?", RoomChoice)


@mcp.tool()
async def book_room(
    date: str,
    attendees: int,
    choice: Annotated[ElicitationResult[RoomChoice], Resolve(pick_room)],
) -> str:
    """Book a meeting room, asking which one when more than one fits."""
    if not isinstance(choice, AcceptedElicitation):
        return "Nothing booked."
    room = choice.data.room
    BOOKED.add((room, date))
    return f"Booked {room} on {date} for {attendees}."


@mcp.resource("rooms://all")
def all_rooms() -> str:
    """Every room the desk knows about."""
    return "\n".join(f"{n}: {r['seats']} seats, floor {r['floor']}" for n, r in ROOMS.items())


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=3001)
