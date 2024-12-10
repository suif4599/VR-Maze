from .base_controller import Controller
from ..engine.base_wrapper import GeneralPoint, AUTO, GeneralVector
from ..engine.base_environment import Render
from ..engine.global_var import set_var, ENTRANCE, get_control_coordinator, set_control_coordinator
from typing import Tuple, Callable, List, Any, Dict
from flask import Flask, request
import requests
import subprocess
from threading import Thread, Lock
from multiprocessing import Process
import argparse
import pickle
import sys
from time import sleep, time
import io
import os
import random
import sys

"""
Note: the web controller will interrupt your argparse
Note: the web controller will cause your debugger not working
"""
def add_argument(*args, **kwargs):
    if not SECRET:
        kwargs["help"] = argparse.SUPPRESS
    PARSER.add_argument(*args, **kwargs)
PARSER = argparse.ArgumentParser()
# PARSER.add_argument("--controlled", action="store_true", help="run the program in web controlled mode, you should never set the parameter")
# PARSER.add_argument("--port", type=int, help="the port to listen to, only valid in controlled mode")
# PARSER.add_argument("--left", action="store_true", help="the port to send left command, only valid in uncontrolled mode")
# PARSER.add_argument("--right", action="store_true", help="the port to send right command, only valid in uncontrolled mode")
# PARSER.add_argument("--sharedfile", type=str, help="the file to store shared variables")
# PARSER.add_argument("--controllermeta", type=str, help="the file to store the controller meta")

SECRET = False
if "--secret" in sys.argv:
    SECRET = True

PARSER.add_argument("--secret", action="store_true", help="show the full help message including the private " \
                    "parameters, you should never use these parameters")

add_argument("--controlled", action="store_true", help="run the program in web controlled mode, you should never set the parameter")
add_argument("--port", type=int, help="the port to listen to, only valid in controlled mode")
add_argument("--left", action="store_true", help="the port to send left command, only valid in uncontrolled mode")
add_argument("--right", action="store_true", help="the port to send right command, only valid in uncontrolled mode")
add_argument("--sharedfile", type=str, help="the file to store shared variables")
add_argument("--controllermeta", type=str, help="the file to store the controller meta")

WEB_CONTROLLED: bool = "--controlled" in sys.argv
set_var("WEB_CONTROLLED", WEB_CONTROLLED)
set_var("PARSER", PARSER)
STDERR = sys.stderr
sys.stderr = io.StringIO()
TEMP = os.getenv("TEMP")
if TEMP is None:
    raise RuntimeError("TEMP is not set")

set_var("PARSER", PARSER)

class SharedVariableDescriptor:
    def __get__(self, instance: "WebController", owner: type) -> Tuple[Any, ...] | Any:
        if WEB_CONTROLLED:
            with open(instance.filename, "rb") as f:
                res = pickle.load(f)
            return res
        else:
            return self.variables # it needn't to do anything in she main process

    def __set__(self, instance: "WebController", value: Tuple[Any, ...] | Any):
        if WEB_CONTROLLED:
            return
        self.variables = value
        instance.filename = os.path.join(TEMP, f"web_controller_{random.randint(1000000, 9999999)}.pkl")
        with open(instance.filename, "wb") as f:
            pickle.dump(value, f)


class WebController:
    "the web controller will tamper controller.camera to control the camera\n"
    "if the program run with --controlled parameter, the WebController will be in mode of receiving control from web\n"
    "if the program run without --controlled parameter, the WebController will be in mode of sending control to web\n"
    "if the web controller is in sending mode, it will tamper the global render to reject the default render loop\n"
    "if the web controller is in receiving mode, it will tamper all other controllers to send commands to the camera"
    SHARED_VARIABLES = SharedVariableDescriptor()
    def __init__(self, controller: Controller, ports: Tuple[int, int] | int = 10111, server_port: int = 10113, 
                 sync_freq: int = 200, fullscreen: bool = False) -> None:
        if WEB_CONTROLLED:
            self.controller_temp = PARSER.parse_args().controllermeta
            with open(self.controller_temp, "rb") as f:
                self.controller = type(controller)(**pickle.load(f))
        else:
            self.controller = controller
            self.controller_temp = f"{TEMP}/web_controller_controller.pkl"
            with open(self.controller_temp, "wb") as f:
                pickle.dump(controller.meta, f)
        self.app = Flask(__name__)
        self.server_port = server_port
        self.ports = ports if isinstance(ports, tuple) else (ports, )
        set_var("PORT_NUM", len(self.ports))
        set_var("WEBCONTROLLER", self)
        self.sync_freq = sync_freq
        self.sync_delta = 1 / sync_freq
        self.fullscreen = fullscreen
        self.filename: str | None = None
        self.no_camera_push = False
        self.supress_control: int = 0
        self.control_lock = Lock()
        self.shared_functions: Dict[str, List[Callable]] = {}
        set_var("NO_OPENGL_FULLSCREEN", fullscreen)
        if WEB_CONTROLLED:
            self.receiver_init()

    def supress(self):
        self.control_lock.acquire()
        self.supress_control += 1
        self.control_lock.release()
    
    def release(self):
        self.control_lock.acquire()
        self.supress_control -= 1
        self.control_lock.release()

    def start(self, render: Render):
        self.camera = render.camera
        if not WEB_CONTROLLED:
            self.sender_init()
        self.controller.start(render)
        if not WEB_CONTROLLED:
            self.controller.camera = self # tamper the camera
    
    def receiver_init(self):
        self.port: int = PARSER.parse_args().port
        self.filename = PARSER.parse_args().sharedfile
        if self.port is None:
            raise RuntimeError("port is not specified")
        self.commands = []
        @self.app.route("/command/<command>", methods=["POST"])
        def command(command: str):
            params = pickle.loads(request.data)
            res = getattr(self.controller.camera, command)(**params)
            return pickle.dumps(res)
        @self.app.route("/set_camera", methods=["POST"])
        def set_camera():
            if not self.camera.suppress_control: # if something strange happens, add "and not self.camera.in_flip" here
                self.camera.position, self.camera.target, self.camera.up, self.camera.tilt = pickle.loads(request.data)
            return "OK"
        @self.app.route("/get_matrix", methods=["GET"])
        def get_matrix():
            return pickle.dumps((self.camera.position, self.camera.target, self.camera.up, get_control_coordinator()[1]))
        @self.app.route("/close", methods=["GET"])
        def close():
            set_var("CLOSE", True)
            return "OK"
        @self.app.route(f"/call_shared/<fname>", methods=["POST"])
        def call_shared(fname: str):
            params: dict = pickle.loads(request.data)
            self.shared_functions[fname][params["ind"]](*params["args"], **params["kwargs"])
        self.flask_thread = Thread(target=self.app.run, kwargs={"port": self.port})
        self.flask_thread.start()

    def sender_init(self):
        set_var("NO_OPENGL", True)
        if self.filename is None:
            raise RuntimeError("Shared variables are not set")
        @self.app.route("/doneleft", methods=["GET"])
        def doneleft():
            self.doneleft = True
            return "OK"
        @self.app.route("/doneright", methods=["GET"])
        def doneright():
            self.doneright = True
            return "OK"
        self.report_url = f"http://localhost:{self.server_port}/done"
        self.flask_thread = Thread(target=self.app.run, kwargs={"port": self.server_port})
        self.subprocesses: List[Process] = []
        python_exe = sys.executable
        command = [python_exe, ENTRANCE, "--controlled", "--sharedfile", self.filename, "--controllermeta", self.controller_temp, "--port"]
        def left():
            if len(self.ports) == 2:
                subprocess.run(command + [str(self.ports[0]), "--left"], check=True)
            else:
                subprocess.run(command + [str(self.ports[0])], check=True)
        self.subprocesses.append(Thread(target=left))
        self.subprocesses[-1].start()
        if len(self.ports) > 1:
            def right():
                subprocess.run(command + [str(self.ports[1]), "--right"], check=True)
            self.subprocesses.append(Thread(target=subprocess.run, args=(command + [str(self.ports[1]), "--right"],), kwargs={"check": True}))
            self.subprocesses[-1].start()
        self.flask_thread.start()
        def flip_camera():
            while True:
                self.push_camera()
                sleep(self.sync_delta)
        self.flip_thread = Thread(target=flip_camera)
        self.flip_thread.start()
        sleep(2)

    
    def send_command(self, command: str, params: dict, awaiting: bool = False, prefix: str = "command") -> Any | None:
        if awaiting:
            self.doneleft = False
            self.doneright = False
        for port in self.ports:
            if awaiting:
                params["report_url"] = self.report_url + ("left" if port == self.ports[0] else "right")
            params_bytes = pickle.dumps(params)
            requests.post(f"http://localhost:{port}/{prefix}/{command}", data=params_bytes, 
                            headers={"Content-Type": "multipart/form-data"})
        if awaiting:
            if len(self.ports) == 2:
                while not self.doneleft or not self.doneright:
                    sleep(self.sync_delta)
            else:
                while not self.doneleft:
                    sleep(self.sync_delta)

    def shared_function(self, func: Callable, name: str | None = None) -> Callable:
        "this decorator will make the function shared between different processes"
        if name is None:
            name = func.__name__
        if name not in self.shared_functions:
            self.shared_functions[name] = [func]
        else:
            self.shared_functions[name].append(func)
        if WEB_CONTROLLED:
            return func
        else:
            ind = len(self.shared_functions[name]) - 1
            def inner(*args, **kwargs):
                self.send_command(name, {"args": args, "kwargs": kwargs, "ind": ind}, prefix="call_shared")
                return func(*args, **kwargs)
            return inner

    def push_camera(self):
        if self.no_camera_push:
            return
        for port in self.ports:
            requests.post(f"http://localhost:{port}/set_camera", 
                          data=pickle.dumps((self.camera.position, self.camera.target, self.camera.up, self.camera.tilt)))

    def close(self):
        for port in self.ports:
            requests.get(f"http://localhost:{port}/close")
        set_var("CLOSE", True)
    
    def show_path(self):
        self.send_command("show_path", {}, awaiting=True)
    
    def hide_path(self):
        self.send_command("hide_path", {}, awaiting=True)
    
    def mark(self):
        self.send_command("mark", {}, awaiting=True)

    def glu_look_at(self, position: GeneralPoint = AUTO, target: GeneralPoint = AUTO, up: GeneralVector = AUTO) -> bool:
        if self.supress_control:
            return False
        return self.camera.glu_look_at(position=position, target=target, up=up)

    def calc_sight(self):
        if self.supress_control:
            return False
        return self.camera.calc_sight()
      
    def set_position(self, position: GeneralPoint) -> bool:
        if self.supress_control:
            return False
        return self.camera.set_position(position)
    
    def look_at(self, theta: float | None = None, phi: float | None = None, tilt: float | None = None) -> None:
        if self.supress_control:
            return
        return self.camera.look_at(theta, phi, tilt)
    
    def move_forward(self, length: float) -> bool:
        if self.supress_control:
            return False
        return self.camera.move_forward(length)
    
    def move_right(self, length: float) -> bool:
        if self.supress_control:
            return False
        return self.camera.move_right(length)
    
    def move_up(self, length: float) -> bool:
        if self.supress_control:
            return False
        return self.camera.move_up(length)
    
    def move_in_plane(self, length: float, theta: float) -> bool:
        if self.supress_control:
            return False
        return self.camera.move_in_plane(length, theta)
    
    def rotate(self, left: float, up: float):
        if self.supress_control:
            return
        return self.camera.rotate(left, up)

    def change_axis(self, in_tube: bool = False):
        if self.supress_control:
            return
        return self.camera.change_axis(in_tube)
