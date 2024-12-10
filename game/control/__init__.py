from ..engine.global_var import get_var
from .base_controller import Controller
from .web_controller import WebController, WEB_CONTROLLED, PARSER, STDERR



if WEB_CONTROLLED:
    class PCController(Controller):
        pass 

    class ArduinoController(Controller):
        pass
else:
    from .PC_controller import PCController
    from .arduino_controller import ArduinoController
    

del WEB_CONTROLLED
