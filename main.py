import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pygame
import random
import json
import requests
import io
import os

from utils import resource_path, play_sound
from logic import QuizGame
from display import OverlayElements

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
        mute_btn = tk.Button(self.canvas, text="Mute Music", font=("Arial", 14), command=self.toggle_sound, bg="#e67e22", fg="#8B0000")
        mute_btn.place(relx=0.5, rely=0.45, anchor="center")
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

if __name__ == "__main__":
    root = tk.Tk()
    app = WorldCapitalsQuiz(root)
    root.mainloop()