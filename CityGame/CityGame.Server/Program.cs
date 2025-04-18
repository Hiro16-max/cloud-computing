using CityGame.Server.Services;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

class Program
{
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);
        builder.Services.AddGrpc();

        var app = builder.Build();

        app.MapGrpcService<CityGameService>();
        app.MapGet("/", () => "gRPC сервер CityGame работает...");

        app.Run();
    }
}
