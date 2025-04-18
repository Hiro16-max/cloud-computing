using CityGame.Server.Services;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddGrpc();

var app = builder.Build();

app.MapGrpcService<CityGameService>();
app.MapGet("/", () => "gRPC сервер CityGame работает...");

app.Run();
