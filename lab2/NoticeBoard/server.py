import json
import socket
import paramiko  # Для работы с SFTP
from data import SFTP_USERNAME, SFTP_PASSWORD
from threading import Thread

FILE_NAME = "messages.json"
PORT = 19001
messages = []

# Настройки для подключения по SFTP
SFTP_HOST = '5.252.22.204'  # IP или доменное имя удаленного сервера
SFTP_PORT = 22  # Стандартный порт для SFTP


# Функция для подключения к SFTP и загрузки/сохранения файла
def sftp_connect():
    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return sftp

def load_messages():
    global messages
    try:
        sftp = sftp_connect()
        # Загружаем файл JSON с удаленного сервера
        sftp.get(FILE_NAME, FILE_NAME)  # Скачиваем файл на локальную машину
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            messages = json.load(file)
        sftp.close()
    except Exception as e:
        print(f"Ошибка при загрузке сообщений: {e}")
        messages = []

def save_messages():
    try:
        sftp = sftp_connect()
        # Сохраняем файл JSON на удаленный сервер
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)
        sftp.put(FILE_NAME, FILE_NAME)  # Загружаем файл обратно на сервер
        sftp.close()
    except Exception as e:
        print(f"Ошибка при сохранении сообщений: {e}")

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
