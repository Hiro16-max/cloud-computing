import socket

# Эмуляция базы данных с использованием словаря
employees = {
    "john": "manager",
    "jane": "steno",
    "jim": "clerk",
    "jack": "salesman"
}


def main():
    port = 12000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('127.0.0.1', port))
    server_socket.listen(5)

    print(f"Server started, listening on port {port}")

    while True:
        # Принимаем новое соединение
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address}")

        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    print(f"Connection closed by client {client_address}")
                    break  # Если данных нет, клиент закрыл соединение
                name = data.decode('ascii')
                job = employees.get(name, "No such employee")
                client_socket.sendall(job.encode('ascii'))
        except Exception as e:
            print(f"Error occurred: {e}")
        finally:
            client_socket.close()
            print(f"Connection with {client_address} closed")

if __name__ == '__main__':
    main()
