# Room Desk, Python

Python SDK 2.0 implementation, built in
[Part 2 of The Stateless MCP](https://mapell.dev/articles/mcp-server-that-asks-a-question).
See the [root README](../README.md) for what this is and, more importantly, for what is
deliberately broken in it.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Two ways to see it work.

**In process, both protocol eras at once.** `client.py` opens two clients against the same
server object, one modern and one legacy, and books a room with each:

```bash
python client.py
```

```
--- modern: 2026-07-28 ---
check_availability: Free on 2026-08-04 for 6: basalt, cinder.
  [asked] Rooms free on 2026-08-04: basalt, cinder. Which one?
book_room: Booked cinder on 2026-08-04 for 6.
--- legacy: 2025-11-25 ---
check_availability: Free on 2026-08-05 for 6: basalt, cinder.
  [asked] Rooms free on 2026-08-05: basalt, cinder. Which one?
book_room: Booked cinder on 2026-08-05 for 6.
```

The tool body is identical in both runs. On the modern connection the question travels inside
the `tools/call` result and comes back on a second call. On the legacy connection the server
opens an `elicitation/create` request of its own. The SDK picks the mechanism.

**Over HTTP, to look at the wire.** Start the server:

```bash
python server.py
```

It listens on `http://127.0.0.1:3001/mcp`. A modern request needs two reverse-DNS keys in
`params._meta` and an `Mcp-Method` header that matches the body:

```bash
curl -s http://127.0.0.1:3001/mcp \
  -H 'Content-Type: application/json' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: server/discover' \
  -d '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{
       "io.modelcontextprotocol/protocolVersion":"2026-07-28",
       "io.modelcontextprotocol/clientCapabilities":{}}}}'
```

A hand-built `tools/call` also needs `Mcp-Name` matching the tool name. Omitting either
header produces `-32020`, the same error as sending a wrong one.

## Files

| File | What it is |
|---|---|
| `server.py` | The server. Two tools and one resource. |
| `client.py` | Drives the server over both protocol eras in one process. |
| `step1_book_room.py` | The deliberately naive first version of `book_room`, which picks the first free room and never asks. Part 2 evolves this into the real one. |

## How the question gets asked

`book_room` takes a parameter it never receives from the model:

```python
choice: Annotated[ElicitationResult[RoomChoice], Resolve(pick_room)]
```

The resolver decides whether a question is needed. One free room and it just books it. Two
and it returns `Elicit(...)`, which the SDK turns into a multi-round-trip. The parameter is
absent from the advertised schema, so a client cannot supply it and cannot get it wrong.

Wrapping it in `ElicitationResult[T]` is what lets the tool body see a decline. Annotate it
as the plain `RoomChoice` and a decline never reaches your code: the call comes back as an
error saying the resolver could not resolve.
