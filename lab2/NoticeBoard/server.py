import json
import socket
from threading import Thread

FILE_NAME = "messages.json"
PORT = 19001
messages = []

def load_messages():
    global messages
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            messages = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Ошибка при загрузке сообщений")
        messages = []

def save_messages():
    try:
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)
    except IOError:
        print("Ошибка при сохранении сообщений")

def handle_client(client_socket):
    try:
        with client_socket:
            print(f"Подключен клиент: {client_socket.getpeername()}")
            while True:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                if data.strip().upper() == "LIST":
                    response = ";".join(messages)
                else:
                    messages.append(data)
                    save_messages()
                    response = f"Message added: \"{data}\""
                client_socket.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Ошибка при обработке запроса: {e}")
    finally:
        print(f"Клиент отключен: {client_socket.getpeername()}")

def start_server():
    load_messages()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(("", PORT))
        server_socket.listen()
        print("Сервер запущен...")
        while True:
            client_socket, _ = server_socket.accept()
            Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
