import socket


def main():
    HOST = "localhost"
    PORT = 19001

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            print("Подключение к серверу...")

            while True:
                user_input = input("Введите сообщение (или оставьте пустым для выхода): ")
                if not user_input:
                    break
                client_socket.sendall(user_input.encode("utf-8"))
                server_response = client_socket.recv(1024).decode("utf-8")
                print("Ответ сервера:", server_response)
    except Exception as e:
        print("Ошибка при подключении к серверу:", e)


if __name__ == "__main__":
    main()