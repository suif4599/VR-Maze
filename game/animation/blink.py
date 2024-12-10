import time
from .base_animation import Animation
import pygame
from threading import Thread
from typing import Tuple, Callable
from ..engine.global_var import get_var

FULL = 1.5

class Blink(Animation):
    "this animation will tamper the render's no_opengl_mainloop"
    def __init__(self, render, duration: int, interval: float = 0.0, callback: Callable = None,
                 supress_control: bool = False, web_controller=None, from_center: bool = False,
                 double_side: bool | None = None):
        "param duration: the duration of the animation, unit: frames of no_opengl_render\n"
        "param interval: after <interval> seconds, the animation will start"
        self.render = render
        self.duration = duration
        self.interval = interval
        self.callback = callback
        self.supress_control = supress_control
        if self.supress_control and web_controller is None:
            raise SyntaxError("web_controller cannot be None if supress_control is True")
        self.controller = web_controller
        self.from_center = from_center
        if from_center:
            self.next = self.next_from_center
        if double_side is None:
            self.double_side = get_var("PORT_NUM") == 2
        else:
            self.double_side = double_side

    def play(self):
        self.scale = 0.0 if self.from_center else FULL
        self.cnt = 0
        self.step = FULL / self.duration # expanding
        Thread(target=super().play).start()
    
    def next_from_center(self) -> bool:
        screen: pygame.Surface = self.render.screen
        size: Tuple[int, int] = self.render.size
        self.scale += self.step
        self.cnt += 1
        if self.double_side:
            pygame.draw.ellipse(screen, (0, 0, 0), 
                                (int(size[0] * (1 - self.scale) / 4), int(size[1] * (1 - self.scale) / 2), 
                                int(size[0] * self.scale / 2), int(size[1] * self.scale)))
            pygame.draw.ellipse(screen, (0, 0, 0), 
                                (int(size[0] * ((1 - self.scale) / 4 + 0.5)), int(size[1] * (1 - self.scale) / 2), 
                                int(size[0] * self.scale / 2), int(size[1] * self.scale)))
        else:
            pygame.draw.ellipse(screen, (0, 0, 0), 
                                (int(size[0] * (1 - self.scale) / 2), int(size[1] * (1 - self.scale) / 2), 
                                int(size[0] * self.scale), int(size[1] * self.scale)))
        if self.cnt >= self.duration and self.step > 0:
            if self.callback:
                self.callback()
            self.step = -self.step # shrinking
        if self.scale < 0:
            if self.supress_control:
                self.controller.release()
            return True
        return False

    def next(self) -> bool:
        "this method should return True if the animation is done"
        screen: pygame.Surface = self.render.screen
        size: Tuple[int, int] = self.render.size
        self.scale -= self.step
        self.cnt += 1
        screen.fill((0, 0, 0))
        if self.double_side:
            pygame.draw.ellipse(screen, self.render.fuchsia, 
                                (int(size[0] * (1 - self.scale) / 4), int(size[1] * (1 - self.scale) / 2), 
                                int(size[0] * self.scale / 2), int(size[1] * self.scale)))
            pygame.draw.ellipse(screen, self.render.fuchsia, 
                                (int(size[0] * ((1 - self.scale) / 4 + 0.5)), int(size[1] * (1 - self.scale) / 2), 
                                int(size[0] * self.scale / 2), int(size[1] * self.scale)))
        else:
            pygame.draw.ellipse(screen, self.render.fuchsia, 
                                (int(size[0] * (1 - self.scale) / 2), int(size[1] * (1 - self.scale) / 2), 
                                int(size[0] * self.scale), int(size[1] * self.scale)))
        if self.cnt >= self.duration and self.step > 0:
            if self.callback:
                self.callback()
            self.step = -self.step # shrinking
        if self.scale > FULL:
            if self.supress_control:
                self.controller.release()
            return True
        return False 