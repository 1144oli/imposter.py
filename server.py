import socket
import select
import random

IP = "localhost"
PORT = 5001
CLIENTSTART = 3

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen()
print(f"Server listening on {IP}:{PORT}")
game_started = False
sockets_list = [server]
clients = {}  

word_list = []
with open('wordlist.txt', newline='') as infile:
    for line in infile:
        word_list.extend(line.strip().split(','))
print(word_list)

def broadcast(message, exclude_socket=None):
    for client_socket in clients:
        if client_socket != exclude_socket:
            client_socket.send(message.encode())

###################
#- Choose imposter#
###################
def start_game():
    players = list(clients.keys())
    imposter_socket = random.choice(players)
    secret_word = random.choice(word_list)

    for player in players:
        if player == imposter_socket:
            player.send("You are the IMPOSTER! Try to blend in.".encode())
            clients[player]["is_imposter"] = True
        else:
            player.send(f"The secret word is: {secret_word}".encode())

    broadcast("Game started! Everyone take turns saying a related word.")


# turn order
turn_index = 0
turn_order = list(clients.keys())

def next_turn():
    global turn_index
    current_socket = turn_order[turn_index]
    current_socket.send("It's your turn! Say a clue:".encode())


## voting
votes = {}
def handle_vote(voter_socket, vote_target_name):
    votes[voter_socket] = vote_target_name
    if len(votes) == len(clients):
        tally_votes()


##endgame
def tally_votes():
    vote_counts = {}
    for vote in votes.values():
        vote_counts[vote] = vote_counts.get(vote, 0) + 1

    most_voted = max(vote_counts, key=vote_counts.get)
    broadcast(f"The group voted out {most_voted}!")

    for socket, data in clients.items():
        if data["name"] == most_voted:
            if data["is_imposter"]:
                broadcast("The imposter was caught! Everyone wins!")
            else:
                broadcast("The imposter survives!")
            break

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
        if len(clients) == CLIENTSTART:
            broadcast(f"{CLIENTSTART} players have joined.\nGAME STARTING NOW...\n")
            game_started = True
            start_game()
        else:
            message = notified_socket.recv(1024)
            if not message:
                print(f"{clients[notified_socket]['name']} disconnected")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue
            print(f"{clients[notified_socket]['name']}: {message.decode()}")


