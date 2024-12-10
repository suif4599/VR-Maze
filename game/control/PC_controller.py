from ..engine import Render
from .base_controller import Controller
from .web_controller import WebController
from typing import Dict
from time import sleep
from ..engine.global_var import get_var, set_var
from ..engine.base_wrapper import Point
from pynput import mouse, keyboard
from threading import Thread

class PCController(Controller):
    def __init__(self, speed: float = 0.01, accute: float = 1.0, 
                 max_delta: int = 50, INVERSE_Y_AXIS=False) -> None:
        self.meta = {"speed": speed, "accute": accute, "max_delta": max_delta, "INVERSE_Y_AXIS": INVERSE_Y_AXIS}
        self.key_down: Dict['str', bool] = {'w': False, 's': False, 'a': False, 'd': False}
        self.speed = speed
        self.accute = accute
        self.max_delta = max_delta
        self.INVERSE_Y_AXIS = INVERSE_Y_AXIS
        self.show_path = False
    
    def start(self, render: Render):
        self.render = render
        self.camera = render.camera
        self.center = (render.size[0] // 2, render.size[1] // 2)
        self.mouse = mouse.Controller()
        def on_press(key):
            try:
                self.key_down[key.char] = True
            except AttributeError: # special key
                if key == keyboard.Key.ctrl_l:
                    if self.show_path:
                        self.show_path = False
                        self.camera.hide_path()
                    else:
                        self.show_path = True
                        self.camera.show_path()
                elif key == keyboard.Key.alt_l:
                    self.camera.mark()
                elif key == keyboard.Key.space:
                    self.camera.change_axis(in_tube=True)
                elif key == keyboard.Key.esc:
                    if isinstance(self.camera, WebController):
                        self.camera.close()
                    else:
                        set_var("CLOSE", True)
        def on_release(key):
            try:
                self.key_down[key.char] = False
            except AttributeError: # special key
                pass
        self.keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.keyboard_listener.start() # it will run in a separate thread
        @self.render.after
        def move_camera(render: Render):
            with mouse.Events() as events:
                while True:
                    # mouse
                    pos = self.mouse.position
                    x, y = pos[0] - self.center[0], pos[1] - self.center[1]
                    if x or y:
                        self.mouse.position = self.center
                        x /= self.render.size[0]
                        y /= self.render.size[1]
                        self.camera.rotate(-x * self.accute, y * self.accute * (1 if self.INVERSE_Y_AXIS else -1))

                    # keyboard 
                    if self.key_down['w']:
                        self.camera.move_forward(self.speed)
                    if self.key_down['s']:
                        self.camera.move_forward(-self.speed)
                    if self.key_down['a']:
                        self.camera.move_right(-self.speed)
                    if self.key_down['d']:
                        self.camera.move_right(self.speed)
                    self.camera.look_at()
                    sleep(0.01)

