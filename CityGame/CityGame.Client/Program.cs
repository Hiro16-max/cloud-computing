using System;
using System.Threading;
using System.Threading.Tasks;
using Grpc.Net.Client;
using CityGame.Proto;

class Program
{
    static async Task Main(string[] args)
    {
        Console.Write("Введите IP или оставьте пустым для localhost: ");
        string address = Console.ReadLine();
        if (string.IsNullOrWhiteSpace(address))
            address = "http://localhost:5146";

        Console.Write("Введите ваше имя: ");
        string name = Console.ReadLine();

        using var channel = GrpcChannel.ForAddress(address);
        var client = new CityGameService.CityGameServiceClient(channel);

        var joinReply = await client.JoinGameAsync(new PlayerRequest { PlayerName = name });
        string playerId = joinReply.PlayerId;
        Console.WriteLine(joinReply.Message);

        while (true)
        {
            Console.WriteLine("Нажмите Enter, когда будете готовы начать игру.");
            Console.ReadLine();
            var readyReply = await client.SetReadyAsync(new ReadyRequest { PlayerId = playerId });
            Console.WriteLine(readyReply.Message);

            bool gameStarted = false;
            while (!gameStarted)
            {
                await Task.Delay(1000);
                var gameState = await client.GetGameStateAsync(new GameRequest { PlayerId = playerId });
                if (!gameState.IsGameOver && !string.IsNullOrEmpty(gameState.CurrentTurnPlayer))
                {
                    Console.WriteLine("\nИгра началась!");
                    gameStarted = true;
                }
                else
                {
                    Console.WriteLine("Ожидание начала игры...");
                }
            }

            bool inGame = true;
            while (inGame)
            {
                var gameState = await client.GetGameStateAsync(new GameRequest { PlayerId = playerId });

                if (gameState.IsGameOver)
                {
                    Console.WriteLine($"\nИгра завершена. Победитель: {gameState.Winner}");
                    inGame = false;
                    break;
                }

                if (gameState.CurrentTurnPlayer == name)
                {
                    Console.WriteLine($"Последний город: {gameState.LastCity}");
                    int timerLine = Console.CursorTop;
                    Console.WriteLine();
                    Console.WriteLine("Введите новый город (10 секунд, можно несколько попыток):");

                    var startTime = DateTime.UtcNow;
                    bool submitted = false;
                    var timerCts = new CancellationTokenSource();

                    _ = Task.Run(async () =>
                    {
                        while (!timerCts.Token.IsCancellationRequested)
                        {
                            int secondsLeft = 10 - (int)(DateTime.UtcNow - startTime).TotalSeconds;
                            if (secondsLeft < 0) break;

                            int left = Console.CursorLeft;
                            int top = Console.CursorTop;

                            Console.SetCursorPosition(0, timerLine);
                            Console.Write($"Осталось времени: {secondsLeft} секунд  ");
                            Console.SetCursorPosition(left, top);

                            await Task.Delay(500);
                        }
                    });

                    while ((DateTime.UtcNow - startTime).TotalSeconds < 10)
                    {
                        if (Console.KeyAvailable)
                        {
                            Console.Write("\n→ ");
                            string city = Console.ReadLine();

                            if (string.IsNullOrWhiteSpace(city)) continue;

                            var response = await client.SubmitCityAsync(new CityRequest
                            {
                                PlayerId = playerId,
                                CityName = city
                            });

                            Console.WriteLine(response.Message);

                            if (string.IsNullOrWhiteSpace(response.Message) ||
                                !response.Message.Contains("не", StringComparison.OrdinalIgnoreCase))
                            {
                                submitted = true;
                                break;
                            }
                        }
                    }

                    timerCts.Cancel();
                    Console.WriteLine();
                    if (!submitted)
                    {
                        Console.WriteLine("Время вышло или не удалось ввести корректный город.");
                        await Task.Delay(1500);
                    }
                }
                else
                {
                    Console.WriteLine($"Ходит игрок: {gameState.CurrentTurnPlayer}");
                    await Task.Delay(2000);
                }
            }
        }
    }
}
