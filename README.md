# Room Desk: an MCP `2026-07-28` server, in Python and C#

A meeting room booking server built twice, once with the Python SDK 2.0 and once with the C#
SDK 2.0, against the MCP `2026-07-28` specification. Both versions implement the same
example, so you can read one against the other.

The `2026-07-28` revision removed the server's ability to call the client in the middle of a
request. A tool that needs an answer from a person can no longer stop and ask. It has to
return the question and get called again with the answer. Booking a room is a small problem
that forces exactly that: two rooms fit, only a person
knows which one is wanted, and the tool cannot finish without being told.

These samples are the reference implementations for Parts 2 and 3 of **The Stateless MCP**:

1. [MCP 2026-07-28 Is Final](https://mapell.dev/articles/mcp-2026-07-28-is-final), what the
   specification changed. No code, and worth reading first if the protocol is new to you.
2. [The MCP server that asks you a question](https://mapell.dev/articles/mcp-server-that-asks-a-question),
   which builds the Python version in `python/`.
3. [The same MCP server in C#, and the three places it differs](https://mapell.dev/articles/mcp-server-in-csharp-three-differences),
   which builds the C# version in `dotnet/`.

## Read this before you copy any of it

**This code is deliberately unsafe. It is written to demonstrate protocol behavior, and
several of its bugs are left in on purpose because the articles are about them.** Do not
lift it into anything that books real rooms.

What is deliberately wrong, in both languages unless noted:

- **No idempotency.** `book_room` has no idempotency key. The `2026-07-28` revision removed
  protocol-level stream resumption, so a dropped connection means the operation is sent
  again, and both versions mishandle that. Python's resolver re-runs and can book a room the
  user rejected. C# honors the stored answer and books the same room again without checking
  whether it is still free.
- **The answer from the client is not validated.** Both versions will book `aurora`, which
  seats four, for a party of six. The capacity rule was never in the elicitation schema, so
  nothing checks it.
- **C# will book a room that does not exist.** Its tool declares a plain string where the
  Python version declares a `Literal`, so answering `atlantis` succeeds. The booking is then
  invisible to `check_availability`, because `atlantis` is not in the room table. This is a
  consequence of what the sample declares, not a limitation of the C# SDK: declare the
  allowed values and you get the same protection Python has.
- **C# does not protect `requestState`.** It goes out as the literal string the handler
  wrote. The Python SDK seals it into an encrypted, authenticated token. The spec requires
  servers to integrity-protect that state wherever it influences authorization or business
  logic, and in C# that work is yours. Nothing in this sample does it.
- **The C# `room` parameter is a compromise, not a recommendation.** It exists so that
  clients which cannot answer a question mid-call still have a way through. Part 2 argues
  against exposing a parameter like that, because a model will fill it in on turns where the
  user never said. Both things are true, and the trade is discussed in Part 3.

If you want a starting point for production code, take the shape of the multi-round-trip
and the `Resolve` or `InputRequiredException` mechanics, then add the idempotency key and
the validation these samples leave out.

## Layout

```
python/    Python SDK 2.0, mcp==2.0.0
dotnet/    C# SDK 2.0, ModelContextProtocol.AspNetCore 2.0.0, net10.0
```

Each directory has its own README with run instructions.

## Versions

Everything here was written and run against these exact versions on 2026-07-29:

| | Version |
|---|---|
| Python SDK | `mcp==2.0.0` on Python 3.11.8 |
| C# SDK | `ModelContextProtocol.AspNetCore 2.0.0` |
| Target framework | `net10.0`, .NET SDK pinned to `10.0.302` by `dotnet/global.json` |
| Protocol revision | `2026-07-28` |

Both SDKs reached `2.0.0` on 2026-07-28, one day before these samples were written, so
expect the surrounding ecosystem to move. If a `2.0.1` has landed by the time you read this,
run the samples before trusting anything the articles say about exact wire output.

## License

MIT. See [LICENSE](LICENSE).
