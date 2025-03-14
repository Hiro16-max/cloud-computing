import socket

def main():
    HOST = input("Введите IP-адрес сервера: ")  # Запрос IP-адреса при запуске клиента
    PORT = int(input("Введите порт для подключения (19002 для сообщений, 19003 для сортировки): "))  # Запрос порта

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            print(f"Подключение к серверу на порт {PORT}...")

            while True:
                if PORT == 19002:  # Если выбран порт для сообщений
                    user_input = input("Введите сообщение (или оставьте пустым для выхода): ")
                    if not user_input:
                        break
                    client_socket.sendall(user_input.encode("utf-8"))
                    server_response = client_socket.recv(1024).decode("utf-8")
                    print("Ответ сервера:", server_response)
                elif PORT == 19003:  # Если выбран порт для сортировки текста
                    user_input = input("Введите текст для сортировки (или оставьте пустым для выхода): ")
                    if not user_input:
                        break
                    client_socket.sendall(user_input.encode("utf-8"))
                    server_response = client_socket.recv(1024).decode("utf-8")
                    print("Ответ сервера (отсортированные слова):\n", server_response)
                else:
                    print("Некорректный порт! Завершаем работу.")
                    break

    except Exception as e:
        print("Ошибка при подключении к серверу:", e)


if __name__ == "__main__":
    main()