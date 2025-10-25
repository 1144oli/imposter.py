import socket
import select
import random

IP = "localhost"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen()
print(f"Server listening on {IP}:{PORT}")

sockets_list = [server]
clients = {}  

def broadcast(message, exclude_socket=None):
    for client_socket in clients:
        if client_socket != exclude_socket:
            client_socket.send(message.encode())

while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    for notified_socket in read_sockets:
        if notified_socket == server:
            client_socket, client_address = server.accept()
            name = client_socket.recv(1024).decode().strip()
            sockets_list.append(client_socket)
            clients[client_socket] = {"name": name, "is_imposter": False}
            print(f"{name} connected from {client_address}")
            broadcast(f"{name} joined the game!", exclude_socket=client_socket)
        else:
            message = notified_socket.recv(1024)
            if not message:
                print(f"{clients[notified_socket]['name']} disconnected")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            print(f"{clients[notified_socket]['name']}: {message.decode()}")

