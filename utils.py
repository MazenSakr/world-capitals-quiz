import sys
import os
import pygame

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def play_sound(file_name):
    try:
        sound = pygame.mixer.Sound(file_name)
        sound.play()
    except:
        pass