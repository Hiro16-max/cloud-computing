import socket

def main():
    ipadress = "127.0.0.1"
    port = 13000

    # Проверяем, был ли передан адрес через аргументы командной строки
    import sys
    if len(sys.argv) > 1:
        ipadress = sys.argv[1]

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        name = input("Name: ")
        if name == "":
            break

        client_socket.sendto(name.encode('ascii'), (ipadress, port))
        data, _ = client_socket.recvfrom(1024)
        job = data.decode('ascii')
        print(job)

if __name__ == '__main__':
    main()
