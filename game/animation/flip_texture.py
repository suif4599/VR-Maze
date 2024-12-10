from .base_animation import Animation
from .change_texture import ChangeTexture
from typing import Tuple, List

class FlipTexture(Animation):
    def __init__(self, render, textures: Tuple, duration: int, interval: float = 0.0, 
                 supress_control: bool = False, web_controller=None, from_center: bool = False):
        "param textures: the textures to be flipped, the present one first\n"
        "param duration: the duration of the animation, unit: frames of no_opengl_render\n"
        "param interval: after <interval> seconds, the animation will start"
        self.render = render
        self.textures = textures
        self.duration = duration
        self.interval = interval
        self.supress_control = supress_control
        self.web_controller = web_controller
        self.from_center = from_center
        self.num = 0
        self.len = len(textures)
        self.animations: List[ChangeTexture] = [ChangeTexture(render, texture, duration, interval, supress_control,
                                                               web_controller, from_center) for texture in textures]
    
    def play(self):
        self.num += 1
        if self.num == self.len:
            self.num = 0
        # self.animation = ChangeTexture(self.render, self.textures[self.num], self.duration, 
        #                                self.interval, self.supress_control, self.web_controller)
        self.animation = self.animations[self.num]
        self.animation.play()
    
    def next(self) -> bool:
        return self.animation.next()