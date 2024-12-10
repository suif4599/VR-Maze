class Controller:
    def __init__(self, *args, **kwargs) -> None:
        pass
    
    def start(self, render):
        self.render = render
        self.camera = render.camera