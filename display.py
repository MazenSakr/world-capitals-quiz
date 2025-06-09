from utils import resource_path, play_sound
from PIL import Image, ImageTk
import tkinter as tk
class OverlayElements:
    def __init__(self, root, canvas):
        self.root = root
        self.canvas = canvas
        self.logo_img = Image.open(resource_path("Virus DS logo_.png")).resize((100, 100))
        self.logo_photo = ImageTk.PhotoImage(self.logo_img)
        self.logo_label = tk.Label(self.root, image=self.logo_photo, bd=0, bg="white")
        self.logo_label.place(relx=0.98, rely=0.88, anchor="se")
        self.signature = tk.Label(self.root, text="Made by VirusDesignStudio-Jasmin Kustura", font=("Arial", 10, "italic"), fg="#8B0000", bg="white")
        self.signature.place(x=-300, rely=0.97, anchor="sw")
        self.signature_direction = 1
        self.animate_logo()
        self.move_signature()

    def animate_logo(self):
        def pulse(scale=1.0, grow=True):
            size = int(100 * scale)
            img = self.logo_img.resize((size, size))
            self.logo_photo = ImageTk.PhotoImage(img)
            self.logo_label.config(image=self.logo_photo)
            next_scale = scale + 0.01 if grow else scale - 0.01
            if next_scale >= 1.1:
                grow = False
            elif next_scale <= 0.9:
                grow = True
            self.root.after(50, lambda: pulse(next_scale, grow))
        pulse()

    def move_signature(self):
        x = self.signature.winfo_x()
        if self.signature_direction == 1:
            if x < self.root.winfo_screenwidth():
                self.signature.place(x=x+2)
            else:
                self.signature_direction = -1
        else:
            if x > -300:
                self.signature.place(x=x-2)
            else:
                self.signature_direction = 1
        self.root.after(30, self.move_signature)