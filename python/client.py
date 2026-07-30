"""Client half of the Room Desk reference implementation."""

import asyncio

from mcp import Client
from mcp.client import ClientRequestContext
from mcp.types import ElicitRequestParams, ElicitResult

from server import mcp


async def answer(context: ClientRequestContext, params: ElicitRequestParams) -> ElicitResult:
    """Stand in for a real UI: always pick cinder."""
    print(f"  [asked] {params.message}")
    return ElicitResult(action="accept", content={"room": "cinder"})


async def main() -> None:
    async with (
        Client(mcp, elicitation_callback=answer) as modern,
        Client(mcp, mode="legacy", elicitation_callback=answer) as legacy,
    ):
        for label, client, date in (("modern", modern, "2026-08-04"), ("legacy", legacy, "2026-08-05")):
            print(f"--- {label}: {client.protocol_version} ---")

            free = await client.call_tool("check_availability", {"date": date, "attendees": 6})
            print("check_availability:", free.content[0].text)

            booked = await client.call_tool("book_room", {"date": date, "attendees": 6})
            print("book_room:", booked.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
