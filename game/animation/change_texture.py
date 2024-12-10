from .base_animation import Animation
from .blink import Blink
from ..engine.global_var import get_var

class ChangeTexture(Animation):
    def __init__(self, render, texture, duration: int, interval: float = 0.0, 
                 supress_control: bool = False, web_controller=None, from_center: bool = False):
        "param duration: the duration of the animation, unit: frames of no_opengl_render\n"
        "param interval: after <interval> seconds, the animation will start"
        self.render = render
        self.texture = texture
        self.duration = duration
        self.interval = interval
        self.supress_control = supress_control
        self.web_controller = web_controller
        self.from_center = from_center
        @web_controller.shared_function
        def change_texture():
            viewer = get_var("GLOBAL_VIEWER")
            viewer.change_texture(self.texture)
        self.blink_animation = Blink(render, duration, interval, change_texture, 
                                     supress_control, web_controller, from_center)
    
    def play(self):
        self.blink_animation.play()
    
    def next(self) -> bool:
        return self.blink_animation.next()

