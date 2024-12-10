from .multi_serial import MultiSerial
import re
import math
import tkinter as tk
from typing import Callable
from time import time

class Rocker:
    "a class that represents a rocker\n"
    "when a callback is registered, the callback will be called when the rocker is updated and be presented with self\n"
    def __init__(self, ser: MultiSerial, time_delta: float = 0.4, strict: bool = True) -> None:
        self.ser = ser
        self.ser.register('Rocker', self.callback)
        self.time_delta = time_delta
        self.x = 0
        self.y = 0
        self.sw = False
        self.double_click = False
        self.callbacks = []
        self.actions = []
        self.oldsw = False
        self.double_old = False
        self.strict = strict
        self.status = True
    
    def callback(self, data: str):
        match = re.match(r"(\d+), (\d+), (\d+)", data) 
        if match:
            x, y, sw = map(int, match.groups())
            self.x = x - 508
            self.y = 520 - y
            self.sw = sw < 10 and self.r < 100
            if not self.double_old or not self.oldsw or not self.sw:
                self.double_old = self.oldsw
                self.oldsw = self.sw
                self.sw = False
            ti = time() - self.time_delta
            i = 0
            for i, (_, t) in enumerate(self.actions):
                if t > ti:
                    break
            if i:
                self.actions = self.actions[i:]
            if self.sw:
                if not self.actions or self.actions[-1][0] == 0: # on release
                    self.actions.append((1, time())) # on click
                    self.status = True
            else:
                if not self.actions or self.actions[-1][0] == 1: # on click
                    self.actions.append((0, time())) # on release
                if self.double_click:
                    self.double_click = False
                    self.actions = []
            if len(self.actions) >= 3 and self.actions[-3][0] == 1 and \
                self.actions[-2][0] == 0 and self.actions[-1][0] == 1:
                self.double_click = True
                self.actions = []
            for callback in self.callbacks:
                callback(self)
        else:
            if self.strict:
                raise ValueError(f"invalid data: {data}")
    
    @property
    def click(self) -> bool:
        if self.status and self.sw:
            self.status = False
            return True
        return False


    def register(self, func: Callable):
        self.callbacks.append(func)

    def __call__(self, callback: Callable) -> Callable:
        self.register(callback)
        return callback

    @property
    def theta(self) -> float | None:
        if self.r < 100:
           return None
        raw = math.atan(self.y / (self.x + 0.5))
        if self.x > -.5:
           return raw
        if self.y > 0:
            return raw + math.pi
        return raw - math.pi
    
    @property
    def r(self):
        return (self.x * self.x + self.y * self.y) ** 0.5

class RockerViewer:
    "start a tkinter window to show the rocker where it shows a big white circle and a small red circle indicating the position of the rocker"
    def __init__(self, rocker: Rocker, win: tk.Tk | None = None, size: int = 300, font: tuple[str, int] = ("Arial", 20)) -> None:
        self.rocker = rocker
        if win is None:
            win = tk.Tk()
            win.title("Rocker Viewer")
            win.geometry("300x300")
        self.win = win
        self.size = size
        self.font = font
    
    def mainloop(self):
        win = self.win
        label = tk.Label(win, text="", width=40, height=2, font=self.font)
        label.pack()
        size = self.size
        half = size // 2
        canvas = tk.Canvas(win, width=self.size, height=self.size)
        canvas.pack()
        def draw():
            label.config(text=f"Rocker: theta = {None if self.rocker.theta is None else round(self.rocker.theta / 3.1415 * 180)}, r = {self.rocker.r: .2f}, sw = {self.rocker.sw}")
            canvas.delete("all")
            color = ("yellow" if self.rocker.double_click else "green") if self.rocker.sw else "white"
            canvas.create_oval(50, 50, size - 50, size - 50, outline="black", fill=color)
            theta = self.rocker.theta
            if theta is None:
                canvas.create_oval(half - 10, half - 10, half + 10, half + 10, outline="black", fill="red")
                win.after(50, draw)
                return
            x = half + (half - 50) * math.cos(theta)
            y = half - (half - 50) * math.sin(theta)
            canvas.create_oval(x - 10, y - 10, x + 10, y + 10, outline="black", fill="red")
            win.after(50, draw)
        draw()
        win.mainloop()