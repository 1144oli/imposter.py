import socket

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('localhost', 5000))
username = input(str("Please input a username:\n>"))
clientsocket.send(username.encode("utf-8"))
