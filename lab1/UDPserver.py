import socket

# Эмуляция базы данных с использованием словаря
employees = {
    "john": "manager",
    "jane": "steno",
    "jim": "clerk",
    "jack": "salesman"
}

def main():
    port = 13000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', port))

    print(f"Server started, servicing on port {port}")

    while True:
        data, address = server_socket.recvfrom(1024)
        name = data.decode('ascii')
        job = employees.get(name, "No such employee")
        server_socket.sendto(job.encode('ascii'), address)

if __name__ == '__main__':
    main()
