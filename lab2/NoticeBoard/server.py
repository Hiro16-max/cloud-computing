import json
import socket
import paramiko
from data import SFTP_USERNAME, SFTP_PASSWORD
from threading import Thread

FILE_NAME = "messages.json"
PORT1 = 19002  # Порт для общения с клиентами (сообщения)
PORT2 = 19003  # Порт для сортировки текста
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


def handle_client_1(client_socket):
    """Обработка клиентов на порту 19002 (работа с сообщениями)"""
    try:
        with client_socket:
            print(f"Подключен клиент: {client_socket.getpeername()} на порт 19002")
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
        print(f"Клиент отключен: {client_socket.getpeername()} на порт 19002")


def handle_client_2(client_socket):
    """Обработка клиентов на порту 19003 для сортировки текста"""
    try:
        with client_socket:
            print(f"Подключен клиент: {client_socket.getpeername()} на порт 19003")
            while True:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                sorted_words = sort_words(data)  # Сортировка слов
                response = "\n".join(sorted_words)  # Каждое слово на новой строке
                client_socket.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"Ошибка при обработке запроса: {e}")
    finally:
        print(f"Клиент отключен: {client_socket.getpeername()} на порт 19003")


def sort_words(text):
    """Функция сортировки слов с учётом регистра и уникальности"""
    words = text.split()
    # Приводим все слова к нижнему регистру и используем множество для уникальности
    words = set(word.lower() for word in words)
    sorted_words = sorted(words)  # Сортировка слов
    return sorted_words


def start_server():
    load_messages()

    # Запускаем два сокет-сервера на разных портах в отдельных потоках
    def listen_port_1():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket_1:
            server_socket_1.bind(("", PORT1))
            server_socket_1.listen()
            print(f"Сервер для сообщений запущен на порту {PORT1}")
            while True:
                client_socket_1, _ = server_socket_1.accept()
                Thread(target=handle_client_1, args=(client_socket_1,)).start()

    def listen_port_2():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket_2:
            server_socket_2.bind(("", PORT2))
            server_socket_2.listen()
            print(f"Сервер для сортировки текста запущен на порту {PORT2}")
            while True:
                client_socket_2, _ = server_socket_2.accept()
                Thread(target=handle_client_2, args=(client_socket_2,)).start()

    # Запускаем два потока для прослушивания портов
    Thread(target=listen_port_1).start()
    Thread(target=listen_port_2).start()


if __name__ == "__main__":
    start_server()
