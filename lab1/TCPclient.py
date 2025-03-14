import socket

def main():
    server_addr = "127.0.0.1"
    port = 12000

    # Проверяем, был ли передан адрес сервера через аргументы командной строки
    import sys
    if len(sys.argv) > 1:
        server_addr = sys.argv[1]

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_addr, port))


    try:
        while True:
            name = input("Name: ")
            if name == "":
                break

            # Отправляем имя серверу
            client_socket.sendall(name.encode('ascii'))

            # Получаем ответ от сервера
            data = client_socket.recv(1024)
            if not data:
                break  # Если данных нет, разрываем соединение

            job = data.decode('ascii')
            print(job)

    finally:
        # Закрываем соединение
        client_socket.close()

if __name__ == '__main__':
    main()
