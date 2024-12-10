from .base_controller import Controller
from ..sensor import *
from ..engine import *
from ..engine.global_var import set_var, get_var
from typing import Tuple
from math import pi
from pynput import keyboard
from .web_controller import WebController

class ArduinoController(Controller):
    def __init__(self, port: str | Tuple[str], baudrate: int | Tuple[int], maxfps: int, 
                 speed: float = 0.01) -> None:
        if get_var("ArduinoController") is not None:
            raise ValueError("There can be only one ArduinoController")
        self.meta = {"port": port, "baudrate": baudrate, "maxfps": maxfps, "speed": speed}
        self.ser = MultiSerial(port, baudrate, maxfps)
        self.rocker = Rocker(self.ser)
        self.mpu = MPU(self.ser)
        self.speed = speed
        @self.mpu
        def _(mpu: MPU):
            self.camera.look_at(mpu.theta, mpu.phi * 0.99, mpu.tilt)
        @self.rocker
        def _(rocker: Rocker):
            if rocker.theta is not None:
                self.camera.move_in_plane(self.speed, rocker.theta - pi / 2)
                pass
            if self.rocker.sw and self.rocker.double_click:
                self.camera.change_axis(in_tube=True)
                self.camera.mark()
            elif self.rocker.click:
                self.camera.mark()
        set_var("ArduinoController", self)
    
    def start(self, render: Render):
        self.render = render
        self.camera = render.camera
        self.ser.start()
        def on_press(key):
            try:
                key.char
            except AttributeError: # special key
                if key == keyboard.Key.esc:
                    if isinstance(self.camera, WebController):
                        self.camera.close()
                    else:
                        set_var("CLOSE", True)
        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        self.keyboard_listener.start() # it will run in a separate thread
    
    def set_theta(self, theta: float) -> None:
        self.mpu.set_theta(theta)

