# import socket
#
# clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# clientsocket.connect(('localhost', 5000))
# username = input(str("Please input a username:\n>"))
# clientsocket.send(username.encode("utf-8"))

import socket
import threading

IP = "localhost"
PORT = 5001

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

username = input("Please input a username:\n> ")
client_socket.send(username.encode("utf-8"))

#listen for message
def receive_messages():
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                print("Disconnected from server.")
                client_socket.close()
                break
            print(f"\n{message}\n> ", end="")
        except:
            print("Error: Connection lost.")
            client_socket.close()
            break

# send them the message
def send_messages():
    while True:
        message = input("> ")
        if message.lower() == "quit":
            client_socket.close()
            break
        client_socket.send(message.encode("utf-8"))

receive_thread = threading.Thread(target=receive_messages, daemon=True)
receive_thread.start()

send_messages()

