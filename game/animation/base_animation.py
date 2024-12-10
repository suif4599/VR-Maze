import time

class Animation:
    "now animations cannot be played with openGL"
    interval: float
    supress_control: bool

    def play(self):
        "this method should set the animation to the initial state, ready for a series of next() calls"
        time.sleep(self.interval)
        if self.supress_control:
            self.controller.supress()
        self.render.add_animation(self)
    
    def next(self) -> bool:
        "this method should return True if the animation is done"
        raise NotImplementedError()