# Room Desk, C#

C# SDK 2.0 implementation on `net10.0`, built in
[Part 3 of The Stateless MCP](https://mapell.dev/articles/mcp-server-in-csharp-three-differences).
See the [root README](../README.md) for what this is and, more importantly, for what is
deliberately broken in it. This version has one flaw the Python one does not: it will book a
room that does not exist.

## Run it

```bash
dotnet build
dotnet run
```

The server listens on `http://127.0.0.1:3002/`. `global.json` pins the .NET SDK to
`10.0.302`, which matters if you have several installed: a bare `dotnet` on a machine with a
newer preview will pick the preview.

Ask it what it speaks:

```bash
curl -s http://127.0.0.1:3002/ \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: server/discover' \
  -d '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{
       "io.modelcontextprotocol/protocolVersion":"2026-07-28",
       "io.modelcontextprotocol/clientCapabilities":{}}}}'
```

Responses come back as `text/event-stream`, where the Python server answers with a plain JSON
body. Both are legal.

## The one line that decides everything

```csharp
.WithHttpTransport(options => options.Stateless = true)
```

`Stateless` reads like a scaling preference. On HTTP it is the precondition for speaking
`2026-07-28` at all, because the revision removed `Mcp-Session-Id` and the `initialize`
handshake. It defaults to `true`, so you get the new protocol unless you turn it off.

Set it to `false` and the server stops advertising `2026-07-28` entirely. Its
`data.supported` list runs from `2024-11-05` to `2025-11-25`. A client doing ordinary version
negotiation settles on the newest thing offered, reports no error, and you have a server that
looks healthy while serving the old protocol. You only see the `-32022` refusal if a client
pins the new revision.

Know that before you set it to `false` for legacy support, which is the documented reason to
set it.

## Files

| File | What it is |
|---|---|
| `Program.cs` | Eleven lines of ASP.NET setup, including the `Stateless` line above. |
| `RoomTools.cs` | The tools. `BookRoom` is the interesting one and runs twice per booking. |
| `RoomDesk.csproj` | `net10.0`, one package reference. |
| `global.json` | Pins the .NET SDK to `10.0.302`. |

## How C# asks a question

Where Python declares a resolver, C# throws:

```csharp
throw new InputRequiredException(inputRequests: ..., requestState: $"{date}:{attendees}");
```

The SDK catches it and turns it into an `InputRequiredResult` with `resultType` of
`"input_required"`. Throwing to produce a successful result reads wrong the first time. It is
control flow, not failure.

`BookRoom` then runs a second time with the answer in `context.Params.InputResponses`, and
you write that branch yourself. The Python SDK writes it for you. The bytes on the wire are
the same, the amount of code in your hands is not. Everything arriving on that second call
came from a client you do not control.

`server.IsMrtrSupported` guards the throw. It is true when `2026-07-28` was negotiated, and
also when the session is stateful under `2025-11-25`, where the SDK bridges the exception to
a legacy `elicitation/create` and calls the handler again, capped at ten rounds.
