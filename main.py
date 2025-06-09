import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pygame
import random
import json
import requests
import io
import os
import threading

from utils import resource_path, play_sound
from logic import QuizGame
from display import OverlayElements

class MultiplayerClient:
    def __init__(self, app):
        self.app = app
        self.sock = None
        self.listener_thread = None
        self.opponent_name = None
        self.my_score = 0
        self.opp_score = 0
        self.current_question = None
        self.total_questions = 0
        self.question_idx = 0
        self.answer_submitted = False
        self.winner = None

    def connect(self, host, port=50007):
        import socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.listener_thread = threading.Thread(target=self.listen, daemon=True)
        self.listener_thread.start()

    def send(self, data):
        msg = json.dumps(data).encode('utf-8')
        self.sock.sendall(len(msg).to_bytes(4, 'big') + msg)

    def recv(self):
        length = int.from_bytes(self.sock.recv(4), 'big')
        data = b''
        while len(data) < length:
            more = self.sock.recv(length - len(data))
            if not more:
                raise ConnectionError('Connection lost')
            data += more
        return json.loads(data.decode('utf-8'))

    def listen(self):
        try:
            while True:
                msg = self.recv()
                self.handle_message(msg)
        except Exception as e:
            self.app.show_error(f"Lost connection to server: {e}")

    def handle_message(self, msg):
        t = msg.get('type')
        if t == 'ask_name':
            self.app.prompt_player_name()
        elif t == 'start':
            self.opponent_name = msg['opponent']
            self.app.show_multiplayer_waiting(self.opponent_name)
        elif t == 'question':
            self.current_question = msg['q']
            self.question_idx = msg['idx']
            self.total_questions = msg['total']
            self.my_score, self.opp_score = msg['scores']
            self.answer_submitted = False
            self.app.show_multiplayer_question()
        elif t == 'result':
            self.my_score = msg['your_score']
            self.opp_score = msg['opp_score']
            self.app.show_multiplayer_result(msg)
        elif t == 'game_over':
            self.winner = msg['winner']
            self.app.show_multiplayer_winner(msg)

    def submit_name(self, name):
        self.send({'name': name})

    def submit_answer(self, answer):
        self.answer_submitted = True
        self.send({'answer': answer})

class WorldCapitalsQuiz:
    def __init__(self, root):
        self.root = root
        self.root.title("World Capitals")
        self.root.attributes('-fullscreen', True)
        self.background_img = Image.open(resource_path("mapa.webp")).resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
        self.background_photo = ImageTk.PhotoImage(self.background_img)
        self.canvas = tk.Canvas(self.root, width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.background_photo, anchor="nw")
        pygame.mixer.init()
        pygame.mixer.music.load(resource_path("backgroundsound.mp3"))
        pygame.mixer.music.play(-1)
        self.sound_on = True
        self.all_data = self.load_data()
        self.overlay = OverlayElements(self.root, self.canvas)
        self.quiz_game = QuizGame(self.root, self.canvas, self.all_data, self.create_main_menu)
        self.create_main_menu()

    def load_data(self):
        try:
            with open(resource_path("countries_all_sample.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
            self.root.destroy()
            return []

    def create_main_menu(self):
        self.clear_screen(keep_overlay=True)
        title = tk.Label(self.canvas, text="🌍 World Capitals 🌍", font=("Arial", 36, "bold"), fg="#8B0000")
        title.place(relx=0.5, rely=0.2, anchor="center")
        start_btn = tk.Button(self.canvas, text="Start Quiz", font=("Arial", 20), command=self.choose_continent, width=20, bg="#3498db", fg="#8B0000")
        start_btn.place(relx=0.5, rely=0.35, anchor="center")
        multi_btn = tk.Button(self.canvas, text="Multiplayer", font=("Arial", 20), command=self.start_multiplayer, width=20, bg="#27ae60", fg="#8B0000")
        multi_btn.place(relx=0.5, rely=0.41, anchor="center")
        mute_btn = tk.Button(self.canvas, text="Mute Music", font=("Arial", 14), command=self.toggle_sound, bg="#e67e22", fg="#8B0000")
        mute_btn.place(relx=0.5, rely=0.48, anchor="center")
        exit_btn = tk.Button(self.canvas, text="Exit", font=("Arial", 14), command=self.root.quit, bg="#c0392b", fg="#8B0000")
        exit_btn.place(relx=0.5, rely=0.55, anchor="center")

    def choose_continent(self):
        self.clear_screen(keep_overlay=True)
        label = tk.Label(self.canvas, text="Choose a Continent", font=("Arial", 28, "bold"), fg="#8B0000")
        label.place(relx=0.5, rely=0.15, anchor="center")
        continents = ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"]
        for i, cont in enumerate(continents):
            btn = tk.Button(self.canvas, text=cont, font=("Arial", 18), width=20,
                            command=lambda c=cont: self.quiz_game.start(c), bg="#1abc9c", fg="#8B0000")
            btn.place(relx=0.5, rely=0.3 + i*0.08, anchor="center")

    def toggle_sound(self):
        pygame.mixer.music.set_volume(0 if self.sound_on else 1)
        self.sound_on = not self.sound_on

    def clear_screen(self, keep_overlay=False):
        for widget in self.canvas.winfo_children():
            if keep_overlay and widget in (self.overlay.logo_label, self.overlay.signature):
                continue
            widget.destroy()

    def start_multiplayer(self):
        self.clear_screen(keep_overlay=True)
        label = tk.Label(self.canvas, text="Enter Server IP to Join Multiplayer", font=("Arial", 24, "bold"), fg="#8B0000")
        label.place(relx=0.5, rely=0.2, anchor="center")
        entry = tk.Entry(self.canvas, font=("Arial", 18), width=20)
        entry.place(relx=0.5, rely=0.3, anchor="center")
        def connect():
            ip = entry.get().strip()
            if not ip:
                messagebox.showerror("Error", "Please enter server IP.")
                return
            self.multiplayer = MultiplayerClient(self)
            try:
                self.multiplayer.connect(ip)
            except Exception as e:
                messagebox.showerror("Connection Failed", str(e))
                self.create_main_menu()
        btn = tk.Button(self.canvas, text="Connect", font=("Arial", 16), command=connect, bg="#27ae60", fg="#8B0000")
        btn.place(relx=0.5, rely=0.4, anchor="center")
        tk.Button(self.canvas, text="Back", font=("Arial", 14), command=self.create_main_menu, bg="#c0392b", fg="#8B0000").place(relx=0.5, rely=0.5, anchor="center")

    def prompt_player_name(self):
        self.clear_screen(keep_overlay=True)
        label = tk.Label(self.canvas, text="Enter Your Name", font=("Arial", 24, "bold"), fg="#8B0000")
        label.place(relx=0.5, rely=0.2, anchor="center")
        entry = tk.Entry(self.canvas, font=("Arial", 18), width=20)
        entry.place(relx=0.5, rely=0.3, anchor="center")
        def submit():
            name = entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter your name.")
                return
            self.multiplayer.submit_name(name)
        btn = tk.Button(self.canvas, text="Submit", font=("Arial", 16), command=submit, bg="#27ae60", fg="#8B0000")
        btn.place(relx=0.5, rely=0.4, anchor="center")

    def show_multiplayer_waiting(self, opponent):
        self.clear_screen(keep_overlay=True)
        label = tk.Label(self.canvas, text=f"Connected! Opponent: {opponent}\nWaiting for game to start...", font=("Arial", 22), fg="#8B0000")
        label.place(relx=0.5, rely=0.3, anchor="center")

    def show_multiplayer_question(self):
        self.clear_screen(keep_overlay=True)
        q = self.multiplayer.current_question
        idx = self.multiplayer.question_idx
        total = self.multiplayer.total_questions
        tk.Label(self.canvas, text=f"Q{idx}/{total}: What is the capital of {q['country']}?", font=("Arial", 22), fg="#8B0000").place(relx=0.5, rely=0.18, anchor="center")
        # Flag
        try:
            import requests, io
            from PIL import Image, ImageTk
            response = requests.get(q['flag'])
            img_data = response.content
            img = Image.open(io.BytesIO(img_data)).resize((120, 80))
            self.flag_img = ImageTk.PhotoImage(img)
            tk.Label(self.canvas, image=self.flag_img).place(relx=0.5, rely=0.28, anchor="center")
        except:
            pass
        # Answers
        answers = [q['capital']]
        all_caps = [x['capital'] for x in self.all_data if x['continent'] == q['continent'] and x['capital'] != q['capital']]
        while len(answers) < 4 and all_caps:
            cap = random.choice(all_caps)
            if cap not in answers:
                answers.append(cap)
        random.shuffle(answers)
        for i, ans in enumerate(answers):
            btn = tk.Button(self.canvas, text=ans, font=("Arial", 16), width=25,
                            command=lambda a=ans: self.submit_multiplayer_answer(a), state="normal" if not self.multiplayer.answer_submitted else "disabled")
            btn.place(relx=0.5, rely=0.42 + i*0.09, anchor="center")
        # Scoreboard
        tk.Label(self.canvas, text=f"You: {self.multiplayer.my_score} | {self.multiplayer.opponent_name}: {self.multiplayer.opp_score}", font=("Arial", 14), fg="#8B0000").place(relx=0.5, rely=0.8, anchor="center")

    def submit_multiplayer_answer(self, answer):
        self.multiplayer.submit_answer(answer)
        self.show_multiplayer_waiting_for_result()

    def show_multiplayer_waiting_for_result(self):
        self.clear_screen(keep_overlay=True)
        tk.Label(self.canvas, text="Waiting for opponent to answer...", font=("Arial", 20), fg="#8B0000").place(relx=0.5, rely=0.5, anchor="center")

    def show_multiplayer_result(self, msg):
        self.clear_screen(keep_overlay=True)
        correct = msg['correct']
        opp_answer = msg['opp_answer']
        result = "Correct!" if self.multiplayer.answer_submitted and correct == self.multiplayer.current_question['capital'] else "Wrong!"
        tk.Label(self.canvas, text=f"{result} The correct answer was: {correct}", font=("Arial", 20), fg="#8B0000").place(relx=0.5, rely=0.3, anchor="center")
        tk.Label(self.canvas, text=f"Opponent answered: {opp_answer}", font=("Arial", 16), fg="#8B0000").place(relx=0.5, rely=0.4, anchor="center")
        tk.Label(self.canvas, text=f"Score: You {msg['your_score']} | {self.multiplayer.opponent_name} {msg['opp_score']}", font=("Arial", 16), fg="#8B0000").place(relx=0.5, rely=0.5, anchor="center")
        tk.Button(self.canvas, text="Next", font=("Arial", 14), command=self.show_multiplayer_waiting_for_next, bg="#3498db", fg="#8B0000").place(relx=0.5, rely=0.6, anchor="center")

    def show_multiplayer_waiting_for_next(self):
        # Just wait for server to send next question
        self.clear_screen(keep_overlay=True)
        tk.Label(self.canvas, text="Waiting for next question...", font=("Arial", 20), fg="#8B0000").place(relx=0.5, rely=0.5, anchor="center")

    def show_multiplayer_winner(self, msg):
        self.clear_screen(keep_overlay=True)
        winner = msg['winner']
        if winner is None:
            text = "It's a tie!"
        elif winner == self.multiplayer.opponent_name:
            text = f"{winner} wins!"
        else:
            text = "You win!"
        tk.Label(self.canvas, text=f"Game Over! {text}", font=("Arial", 28, "bold"), fg="#8B0000").place(relx=0.5, rely=0.3, anchor="center")
        tk.Label(self.canvas, text=f"Final Score: You {msg['your_score']} | {self.multiplayer.opponent_name} {msg['opp_score']}", font=("Arial", 18), fg="#8B0000").place(relx=0.5, rely=0.4, anchor="center")
        tk.Button(self.canvas, text="Back to Menu", font=("Arial", 16), command=self.create_main_menu, bg="#3498db", fg="#8B0000").place(relx=0.5, rely=0.6, anchor="center")

    def show_error(self, msg):
        messagebox.showerror("Error", msg)
        self.create_main_menu()

if __name__ == '__main__':
    root = tk.Tk()
    app = WorldCapitalsQuiz(root)
    root.mainloop()