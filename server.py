import socket
import threading
import json
import random
import time

HOST = '0.0.0.0'
PORT = 50007

with open('countries_all_sample.json', 'r', encoding='utf-8') as f:
    ALL_QUESTIONS = [q for q in json.load(f) if 'country' in q and 'capital' in q and 'continent' in q]

class Player:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.score = 0
        self.name = None
        self.ready = False
        self.answer = None
        self.finished = False

def send(conn, data):
    msg = json.dumps(data).encode('utf-8')
    conn.sendall(len(msg).to_bytes(4, 'big') + msg)

def recv(conn):
    length = int.from_bytes(conn.recv(4), 'big')
    data = b''
    while len(data) < length:
        more = conn.recv(length - len(data))
        if not more:
            raise ConnectionError('Connection lost')
        data += more
    return json.loads(data.decode('utf-8'))

def handle_player(player, other_player, questions, state):
    try:
        # Get player name
        send(player.conn, {'type': 'ask_name'})
        player.name = recv(player.conn)['name']
        player.ready = True
        while not other_player.ready:
            time.sleep(0.1)
        send(player.conn, {'type': 'start', 'opponent': other_player.name})
        for idx, q in enumerate(questions):
            send(player.conn, {'type': 'question', 'q': q, 'idx': idx+1, 'total': len(questions), 'scores': [player.score, other_player.score]})
            ans = recv(player.conn)
            player.answer = ans.get('answer')
            player.finished = True
            while not other_player.finished:
                time.sleep(0.05)
            # After both answered, send result
            correct = q['capital']
            if player.answer == correct:
                player.score += 1
            send(player.conn, {'type': 'result', 'correct': correct, 'your_score': player.score, 'opp_score': other_player.score, 'opp_answer': other_player.answer})
            player.finished = False
            other_player.finished = False
        # Game over
        winner = None
        if player.score > other_player.score:
            winner = player.name
        elif player.score < other_player.score:
            winner = other_player.name
        # Wait for both players to finish sending all results before sending game_over
        player.finished = True
        while not other_player.finished:
            time.sleep(0.05)
        send(player.conn, {'type': 'game_over', 'your_score': player.score, 'opp_score': other_player.score, 'winner': winner})
        # Wait for both to send game_over before closing connection
        player.finished = False
        while other_player.finished:
            time.sleep(0.05)
    except Exception as e:
        print(f"Player {player.addr} error: {e}")
    finally:
        player.conn.close()

def main():
    print(f"Server listening on {HOST}:{PORT}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        players = []
        while len(players) < 2:
            conn, addr = s.accept()
            print(f"Player connected from {addr}")
            players.append(Player(conn, addr))
        # Pick 10 random questions from a random continent
        continent = random.choice(['Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania'])
        questions = [q for q in ALL_QUESTIONS if q['continent'] == continent]
        questions = random.sample(questions, min(10, len(questions)))
        state = {}
        t1 = threading.Thread(target=handle_player, args=(players[0], players[1], questions, state))
        t2 = threading.Thread(target=handle_player, args=(players[1], players[0], questions, state))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print("Game finished.")

if __name__ == '__main__':
    main()
