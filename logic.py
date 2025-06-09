from utils import resource_path, play_sound
import tkinter as tk
from PIL import Image, ImageTk
import requests
import random
import io
from tkinter import messagebox

class QuizGame:
    def __init__(self, parent, canvas, all_data, on_end):
        self.parent = parent
        self.canvas = canvas
        self.all_data = all_data
        self.on_end = on_end
        self.score = 0
        self.time_left = 10
        self.timer_id = None
        self.current_question = {}
        self.questions = []
        self.continent = ""
        self.timer_label = None

    def start(self, continent):
        self.continent = continent
        self.questions = [q for q in self.all_data if q["continent"] == continent]
        if len(self.questions) < 4:
            messagebox.showwarning("Not enough questions", f"Not enough data for {continent}")
            self.on_end()
            return
        self.score = 0
        self.next_question()

    def next_question(self):
        self.clear_screen(keep_overlay=True)
        self.time_left = 10
        self.current_question = random.choice(self.questions)
        question_text = f"What is the capital of {self.current_question['country']}?"
        tk.Label(self.canvas, text=question_text, font=("Arial", 24), fg="#8B0000").place(relx=0.5, rely=0.2, anchor="center")
        self.load_flag(self.current_question["flag"])
        answers = [self.current_question["capital"]]
        while len(answers) < 4:
            random_cap = random.choice(self.questions)["capital"]
            if random_cap not in answers:
                answers.append(random_cap)
        random.shuffle(answers)
        for i, ans in enumerate(answers):
            tk.Button(self.canvas, text=ans, font=("Arial", 16), width=25,
                      command=lambda a=ans: self.check_answer(a)).place(relx=0.5, rely=0.4 + i*0.08, anchor="center")
        tk.Label(self.canvas, text=f"Score: {self.score}", font=("Arial", 14), fg="#8B0000").place(relx=0.5, rely=0.75, anchor="center")
        self.timer_label = tk.Label(self.canvas, text=f"Time: {self.time_left}", font=("Arial", 14), fg="#8B0000")
        self.timer_label.place(relx=0.5, rely=0.8, anchor="center")
        tk.Button(self.canvas, text="End Quiz", font=("Arial", 12), command=self.on_end, bg="#e74c3c", fg="#8B0000").place(relx=0.5, rely=0.9, anchor="center")
        self.update_timer()

    def load_flag(self, url):
        try:
            response = requests.get(url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data)).resize((150, 100))
            self.flag_img = ImageTk.PhotoImage(img)
            flag_label = tk.Label(self.canvas, image=self.flag_img)
            flag_label.place(relx=0.5, rely=0.3, anchor="center")
        except:
            pass

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.config(text=f"Time: {self.time_left}")
            self.timer_id = self.parent.after(1000, self.update_timer)
        else:
            self.check_answer("")

    def check_answer(self, answer):
        if self.timer_id:
            self.parent.after_cancel(self.timer_id)
            self.timer_id = None
        correct = self.current_question["capital"]
        if answer == correct:
            self.score += 1
            play_sound(resource_path("correct.wav"))
            messagebox.showinfo("Correct", "That's correct! 🎉")
        else:
            play_sound(resource_path("wrong.wav"))
            messagebox.showerror("Wrong", f"Wrong answer! The capital of {self.current_question['country']} is {correct}.")
        self.next_question()

    def clear_screen(self, keep_overlay=False):
        for widget in self.canvas.winfo_children():
            if keep_overlay and hasattr(self.parent, "overlay") and widget in (self.parent.overlay.logo_label, self.parent.overlay.signature):
                continue
            widget.destroy()
