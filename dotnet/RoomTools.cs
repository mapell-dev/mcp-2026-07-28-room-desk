using System.ComponentModel;
using ModelContextProtocol.Protocol;
using ModelContextProtocol.Server;

namespace RoomDesk;

[McpServerToolType]
public sealed class RoomTools
{
    private static readonly Dictionary<string, (int Seats, int Floor)> Rooms = new()
    {
        ["aurora"] = (4, 2),
        ["basalt"] = (8, 2),
        ["cinder"] = (8, 5),
    };

    private static readonly HashSet<(string Room, string Date)> Booked = new()
    {
        ("basalt", "2026-08-03"),
    };

    private static List<string> FreeRooms(string date, int attendees) =>
        Rooms.Where(r => r.Value.Seats >= attendees && !Booked.Contains((r.Key, date)))
             .Select(r => r.Key)
             .Order()
             .ToList();

    [McpServerTool, Description("List the meeting rooms free on a date that seat this many people.")]
    public static string CheckAvailability(
        [Description("The date, as YYYY-MM-DD")] string date,
        [Description("How many people need a seat")] int attendees)
    {
        var free = FreeRooms(date, attendees);
        return free.Count == 0
            ? $"No room on {date} seats {attendees}."
            : $"Free on {date} for {attendees}: {string.Join(", ", free)}.";
    }

    [McpServerTool, Description("Book a meeting room, asking which one when more than one fits.")]
    public static string BookRoom(
        McpServer server,
        RequestContext<CallToolRequestParams> context,
        [Description("The date, as YYYY-MM-DD")] string date,
        [Description("How many people need a seat")] int attendees,
        [Description("Which room to book. Only needed by clients that cannot answer a question mid-call.")]
        string? room = null)
    {
        var free = FreeRooms(date, attendees);
        if (free.Count == 0)
        {
            return $"No room on {date} seats {attendees}.";
        }

        // The non-interactive path: a caller that cannot do a multi-round-trip names the room
        // up front. Deliberately trusted without validation, exactly like the elicited answer
        // below, because the tutorial's point is that neither one is checked for you.
        if (room is not null)
        {
            Booked.Add((room, date));
            return $"Booked {room} on {date} for {attendees}.";
        }

        // The second call: the client answered the question we asked below.
        if (context.Params?.InputResponses?.TryGetValue("room", out var response) is true)
        {
            var elicited = response.Deserialize(InputResponse.ElicitResultJsonTypeInfo);
            if (elicited?.IsAccepted is not true)
            {
                return "Nothing booked.";
            }

            var picked = elicited.Content?.TryGetValue("room", out var value) is true
                ? value.GetString()
                : null;
            picked ??= free[0];

            Booked.Add((picked, date));
            return $"Booked {picked} on {date} for {attendees}.";
        }

        // Only one room fits, so there is nothing to ask about.
        if (free.Count == 1)
        {
            Booked.Add((free[0], date));
            return $"Booked {free[0]} on {date} for {attendees}.";
        }

        if (!server.IsMrtrSupported)
        {
            return $"More than one room fits ({string.Join(", ", free)}). "
                 + "Resend with the room you want, or connect with a client that negotiates 2026-07-28.";
        }

        // The first leg: return the question instead of calling back to the client.
        throw new InputRequiredException(
            inputRequests: new Dictionary<string, InputRequest>
            {
                ["room"] = InputRequest.ForElicitation(new ElicitRequestParams
                {
                    Message = $"Rooms free on {date}: {string.Join(", ", free)}. Which one?",
                    RequestedSchema = new()
                    {
                        Properties =
                        {
                            ["room"] = new ElicitRequestParams.StringSchema
                            {
                                Title = "Room",
                                Description = "Which room to book",
                            },
                        },
                    },
                }),
            },
            requestState: $"{date}:{attendees}");
    }
}
