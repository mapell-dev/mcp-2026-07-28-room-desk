using RoomDesk;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddMcpServer()
    .WithHttpTransport(options => options.Stateless = true)
    .WithTools<RoomTools>();

var app = builder.Build();
app.MapMcp();
app.Run("http://127.0.0.1:3002");
