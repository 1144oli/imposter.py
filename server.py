import socket
import select
import random
import time

IP = "localhost"
PORT = 5001
MIN_PLAYERS = 3

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((IP, PORT))
server.listen()
print(f"Server listening on {IP}:{PORT}")

sockets_list = [server]
clients = {}
word_list = []

# Game State
game_state = "WAITING"  
turn_order = []
turn_index = 0
votes = {}
secret_word = ""

def load_words():
    global word_list
    try:
        with open('wordlist.txt', newline='') as infile:
            word_list = [word for line in infile for word in line.strip().split(',') if word]
        print(f"Loaded {len(word_list)} words.")
    except FileNotFoundError:
        print("Error: wordlist.txt not found. The game cannot start.")
        word_list = ["cat", "dog", "car", "house", "tree", "sun"]
        print(f"Using fallback word list: {word_list}")

def broadcast(message, exclude_socket=None):
    for client_socket in clients:
        if client_socket != exclude_socket:
            try:
                client_socket.send(message.encode())
            except:
                remove_client(client_socket)

def remove_client(client_socket):
    if client_socket in sockets_list:
        sockets_list.remove(client_socket)
    if client_socket in clients:
        print(f"{clients[client_socket]['name']} has disconnected.")
        del clients[client_socket]
        if game_state != "WAITING":
            reset_game("A player disconnected, the game has been reset.")

def reset_game(reason=""):
    global game_state, turn_order, turn_index, votes, secret_word
    if reason:
        broadcast(reason)
    game_state = "WAITING"
    turn_order = []
    turn_index = 0
    votes = {}
    secret_word = ""
    for client_data in clients.values():
        client_data["is_imposter"] = False
    print("Game has been reset. Waiting for players...")
    broadcast(f"Waiting for {MIN_PLAYERS} players to start...")

def start_game():
    global game_state, secret_word, turn_order, turn_index
    game_state = "ROUND"
    print("--- GAME STARTING ---")
    players = list(clients.keys())
    random.shuffle(players)
    turn_order = players
    turn_index = 0
    imposter_socket = random.choice(players)
    secret_word = random.choice(word_list)

    player_names = [clients[p]['name'] for p in players]
    broadcast(f"Game starting with players: {', '.join(player_names)}")
    time.sleep(1)

    for player in players:
        clients[player]["is_imposter"] = (player == imposter_socket)
        try:
            if player == imposter_socket:
                player.send("You are the IMPOSTER! Try to blend in.".encode())
            else:
                player.send(f"The secret word is: {secret_word}".encode())
            time.sleep(0.1)
        except:
            remove_client(player)
    
    print(f"Secret word is '{secret_word}'. {clients[imposter_socket]['name']} is the imposter.")
    next_turn()

def next_turn():
    global turn_index, game_state
    if turn_index < len(turn_order):
        current_socket = turn_order[turn_index]
        current_player_name = clients[current_socket]['name']
        broadcast(f"It's {current_player_name}'s turn to say a word.")
        try:
            current_socket.send("It's your turn! Say a clue word:".encode())
        except:
            remove_client(current_socket)
    else:
        game_state = "VOTING"
        print("--- VOTING PHASE ---")
        player_names = [data['name'] for data in clients.values()]
        broadcast(f"All clues have been given! Time to vote. Use 'vote <player_name>'.\nPlayers: {', '.join(player_names)}")

def handle_vote(voter_socket, vote_target_name):
    global votes
    if voter_socket in votes:
        voter_socket.send("You have already voted.".encode())
        return

    target_socket = None
    for sock, data in clients.items():
        if data['name'].lower() == vote_target_name.lower():
            target_socket = sock
            break
    
    if target_socket:
        votes[voter_socket] = clients[target_socket]['name']
        broadcast(f"{clients[voter_socket]['name']} has voted.")
        if len(votes) == len(clients):
            tally_votes()
    else:
        voter_socket.send(f"Player '{vote_target_name}' not found.".encode())

def tally_votes():
    global game_state
    print("--- TALLYING VOTES ---")
    vote_counts = {}
    for vote in votes.values():
        vote_counts[vote] = vote_counts.get(vote, 0) + 1
    
    if not vote_counts:
        reset_game("No votes were cast. Game reset.")
        return

    most_voted_name = max(vote_counts, key=vote_counts.get)
    broadcast(f"The group has voted out {most_voted_name}!")

    voted_out_imposter = False
    for sock, data in clients.items():
        if data["name"] == most_voted_name:
            if data["is_imposter"]:
                voted_out_imposter = True
            break
    
    time.sleep(1)
    if voted_out_imposter:
        broadcast(f"{most_voted_name} was the Imposter! The Crew wins!")
    else:
        broadcast(f"{most_voted_name} was not the Imposter! The Imposter wins!")
    
    game_state = "FINISHED"
    print("--- GAME FINISHED ---")
    time.sleep(5)
    reset_game()

def handle_client_message(client_socket, message):
    global turn_index
    player_name = clients[client_socket]['name']

    if game_state == "ROUND":
        if client_socket == turn_order[turn_index]:
            broadcast(f"{player_name}: {message}")
            turn_index += 1
            next_turn()
        else:
            client_socket.send("It's not your turn.".encode())
    
    elif game_state == "VOTING":
        if message.lower().startswith("vote "):
            parts = message.split(" ", 1)
            if len(parts) == 2:
                handle_vote(client_socket, parts[1].strip())
            else:
                client_socket.send("Invalid vote command. Use 'vote <player_name>'".encode())
        else:
            client_socket.send("It's voting time. Please vote or wait for the results.".encode())
    
    else: 
        broadcast(f"[{player_name}]: {message}")
####################
# Main Server loop #
####################
load_words()
reset_game()

while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
    if str(input('>')) == 'start':
        broadcast("Minimum players reached. Starting game in 5 seconds...")
        time.sleep(5)
        start_game()

    for notified_socket in read_sockets:
        if notified_socket == server:
            client_socket, client_address = server.accept()
            
            try:
                name = client_socket.recv(1024).decode().strip()
                if not name:
                    continue

                sockets_list.append(client_socket)
                clients[client_socket] = {"name": name, "is_imposter": False}
                print(f"Accepted new connection from {client_address[0]}:{client_address[1]} as {name}")
                
                if game_state != "WAITING":
                    client_socket.send("A game is already in progress. Please wait.".encode())
                else:
                    broadcast(f"{name} has joined the lobby.")
                    if len(clients) >= MIN_PLAYERS:
                        broadcast("Minimum players reached. Starting game in 5 seconds...")
                        time.sleep(5)
                        start_game()
            except:
                continue

        else:
            try:
                message_data = notified_socket.recv(1024)
                if not message_data:
                    remove_client(notified_socket)
                else:
                    handle_client_message(notified_socket, message_data.decode().strip())
            except:
                remove_client(notified_socket)

    for notified_socket in exception_sockets:
        remove_client(notified_socket)
