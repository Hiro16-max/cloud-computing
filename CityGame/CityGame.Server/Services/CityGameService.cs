using CityGame.Proto;
using Grpc.Core;
using static CityGame.Proto.CityGameService;

namespace CityGame.Server.Services;

public class CityGameService : CityGameServiceBase
{
    private static readonly List<string> AllCities = new()
    {
        "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", "Нижний Новгород", "Челябинск", "Самара",
        "Омск", "Ростов-на-Дону", "Уфа", "Красноярск", "Пермь", "Воронеж", "Волгоград", "Саратов", "Тюмень", "Тольятти",
        "Ижевск", "Барнаул", "Ульяновск", "Иркутск", "Хабаровск", "Ярославль", "Владивосток", "Махачкала", "Томск",
        "Оренбург", "Кемерово", "Новокузнецк", "Рязань", "Астрахань", "Набережные Челны", "Пенза", "Липецк", "Киров",
        "Чебоксары", "Балашиха", "Калининград", "Курск", "Улан-Удэ", "Ставрополь", "Тула", "Сочи", "Тверь", "Магнитогорск",
        "Иваново", "Брянск", "Белгород", "Сургут", "Владимир", "Нижний Тагил", "Архангельск", "Калуга", "Анапа"
    };

    private static List<string> UsedCities = new();
    private static List<string> PlayerOrder = new();
    private static Dictionary<string, string> PlayerNames = new();
    private static Dictionary<string, DateTime> PlayerLastTurnTime = new();
    private static HashSet<string> ReadyPlayers = new();
    private static int currentTurnIndex = 0;
    private static bool gameStarted = false;
    private static string lastCity = "";
    private static string winner = "";
    private static readonly object locker = new();
    private static readonly int timeoutSeconds = 10;
    private static bool awaitingReadiness = true;

    public CityGameService()
    {
        _ = MonitorTurnsAsync();
    }

    public override Task<JoinReply> JoinGame(PlayerRequest request, ServerCallContext context)
    {
        lock (locker)
        {
            string playerId = Guid.NewGuid().ToString();
            PlayerNames[playerId] = request.PlayerName;
            if (!PlayerOrder.Contains(playerId))
                PlayerOrder.Add(playerId);
            PlayerLastTurnTime[playerId] = DateTime.UtcNow;

            Console.WriteLine($"Игрок {request.PlayerName} присоединился. Всего: {PlayerNames.Count}");

            return Task.FromResult(new JoinReply
            {
                PlayerId = playerId,
                Message = $"Добро пожаловать, {request.PlayerName}! Ожидайте начала игры.",
                GameStarted = gameStarted
            });
        }
    }

    public override Task<GameStateReply> GetGameState(GameRequest request, ServerCallContext context)
    {
        lock (locker)
        {
            return Task.FromResult(BuildGameState());
        }
    }

    public override Task<GameStateReply> SubmitCity(CityRequest request, ServerCallContext context)
    {
        lock (locker)
        {
            if (!gameStarted || !string.IsNullOrEmpty(winner))
                return Task.FromResult(BuildGameState("Игра ещё не началась или уже завершена."));

            if (PlayerOrder.Count == 0 || currentTurnIndex >= PlayerOrder.Count)
                return Task.FromResult(BuildGameState("Невозможно определить текущего игрока."));

            if (PlayerOrder[currentTurnIndex] != request.PlayerId)
                return Task.FromResult(BuildGameState("Сейчас не ваш ход."));

            string city = request.CityName.Trim();

            if (UsedCities.Contains(city, StringComparer.OrdinalIgnoreCase))
                return Task.FromResult(BuildGameState("Город уже был назван."));

            if (!AllCities.Contains(city, StringComparer.OrdinalIgnoreCase))
                return Task.FromResult(BuildGameState("Такого города нет в списке."));

            if (!string.IsNullOrEmpty(lastCity))
            {
                char lastChar = GetLastValidChar(lastCity);
                char firstChar = char.ToLower(city[0]);

                if (firstChar != char.ToLower(lastChar))
                    return Task.FromResult(BuildGameState($"Город должен начинаться на букву '{char.ToUpper(lastChar)}'"));
            }

            UsedCities.Add(city);
            lastCity = city;
            PlayerLastTurnTime[request.PlayerId] = DateTime.UtcNow;

            AdvanceTurn();
            return Task.FromResult(BuildGameState($"{PlayerNames[request.PlayerId]} назвал город {city}"));
        }
    }

    private void AdvanceTurn()
    {
        currentTurnIndex = (currentTurnIndex + 1) % PlayerOrder.Count;
        PlayerLastTurnTime[PlayerOrder[currentTurnIndex]] = DateTime.UtcNow;
    }

    private async Task MonitorTurnsAsync()
    {
        while (true)
        {
            await Task.Delay(1000);

            lock (locker)
            {
                if (awaitingReadiness)
                {
                    ReadyPlayers.RemoveWhere(id => !PlayerNames.ContainsKey(id));

                    if (ReadyPlayers.Count >= 2 && ReadyPlayers.All(PlayerNames.ContainsKey))
                    {
                        StartNewGame();
                        awaitingReadiness = false;
                    }
                    continue;
                }

                if (!gameStarted || PlayerOrder.Count <= 1)
                    continue;

                string currentPlayerId = PlayerOrder[currentTurnIndex];
                if (!PlayerLastTurnTime.ContainsKey(currentPlayerId))
                    continue;

                if ((DateTime.UtcNow - PlayerLastTurnTime[currentPlayerId]).TotalSeconds > timeoutSeconds)
                {
                    Console.WriteLine($"Игрок {PlayerNames[currentPlayerId]} выбыл по таймауту.");

                    int removedIndex = currentTurnIndex;

                    // НЕ удаляем игрока полностью, просто пропускаем его в текущем раунде
                    currentTurnIndex = (currentTurnIndex + 1) % PlayerOrder.Count;

                    if (PlayerOrder.Count == 2)
                    {
                        string remainingPlayer = PlayerOrder.First(id => id != currentPlayerId);
                        winner = PlayerNames[remainingPlayer];
                        Console.WriteLine($"Победитель: {winner}");
                        gameStarted = false;

                        ReadyPlayers.Clear();

                        _ = Task.Run(async () =>
                        {
                            await Task.Delay(3000);
                            lock (locker)
                            {
                                ResetGame();
                            }
                        });

                        continue;
                    }

                    PlayerLastTurnTime[PlayerOrder[currentTurnIndex]] = DateTime.UtcNow;
                }
            }
        }
    }

    private void StartNewGame()
    {
        UsedCities = new();
        lastCity = "";
        winner = "";
        gameStarted = true;
        currentTurnIndex = 0;

        foreach (var playerId in PlayerOrder)
        {
            PlayerLastTurnTime[playerId] = DateTime.UtcNow;
        }

        Console.WriteLine("Игра началась! Игроки: " + string.Join(", ", PlayerNames.Values));
    }

    private void ResetGame()
    {
        UsedCities = new();
        lastCity = "";
        winner = "";
        gameStarted = false;
        awaitingReadiness = true;
        currentTurnIndex = 0;

        ReadyPlayers.Clear();

        Console.WriteLine("Игра сброшена. Ожидание готовности.");
    }

    private static char GetLastValidChar(string city)
    {
        for (int i = city.Length - 1; i >= 0; i--)
        {
            char ch = city[i];
            if (ch != 'ь' && ch != 'ъ' && ch != 'ы')
                return ch;
        }
        return city[^1];
    }

    public override Task<ReadyReply> SetReady(ReadyRequest request, ServerCallContext context)
    {
        lock (locker)
        {
            ReadyPlayers.Add(request.PlayerId);
            return Task.FromResult(new ReadyReply
            {
                Message = "Вы отметились как готовый игрок."
            });
        }
    }

    private GameStateReply BuildGameState(string message = "")
    {
        string currentPlayerId = (PlayerOrder.Count > 0 && currentTurnIndex < PlayerOrder.Count) ? PlayerOrder[currentTurnIndex] : "";
        string currentPlayerName = PlayerNames.ContainsKey(currentPlayerId) ? PlayerNames[currentPlayerId] : "";

        return new GameStateReply
        {
            CurrentTurnPlayer = gameStarted ? currentPlayerName : "",
            LastCity = lastCity,
            Message = message,
            IsGameOver = !string.IsNullOrEmpty(winner),
            Winner = winner,
            Players = { PlayerNames.Values },
            UsedCities = { UsedCities }
        };
    }
}
