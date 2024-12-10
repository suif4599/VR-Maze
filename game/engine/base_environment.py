from OpenGL.GL import *
from OpenGL.GLU import *
from .base_wrapper import *
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, NOFRAME, FULLSCREEN
from math import sin, cos, pi
from typing import Callable
from types import MethodType
from threading import Thread
import os
from .global_var import set_var, get_var, get_max_brightness_level, set_control_coordinator, \
    get_control_coordinator
from typing import List, Tuple
from .useful_object import Tube, FloatingBlock
from argparse import ArgumentParser
import win32gui
import win32con
import win32api
from time import sleep, time
import requests
from ..animation.base_animation import Animation


HALF_PI = pi / 2 - 1e-3



class Camera:
    EXIST = False
    position: Point
    target: Point
    up: Vector
    render: "Render"
    def __init__(self, position: GeneralPoint, target: GeneralPoint, up: GeneralVector, 
                 position_refiner: Callable[[GeneralPoint], Tuple[GeneralPoint, bool]] | None = None,
                 ipd: float = 0.06, concentrate: float = 0.85) -> None:
        if Camera.EXIST:
            raise RuntimeError("Cannot create more than one camera")
        if position_refiner is None:
            def position_refiner(position: GeneralPoint) -> Tuple[GeneralPoint, bool]:
                return position, False
        self.position_refiner = position_refiner
        self.glu_look_at(position, target, up)
        arrow = self.target - self.position
        self.theta = arrow.theta
        self.phi = arrow.phi
        self.suppress_control = False
        self.in_flip = False
        self.left_sided = get_var("PARSER").parse_args().left
        self.right_sided = get_var("PARSER").parse_args().right
        Camera.EXIST = True
        self.half_ipd = ipd / 2
        self.concentrate = concentrate
        self.tilt = 0. # the tilt angle of the camera, only valid when arduino sensor is on

    
    def glu_look_at(self, position: GeneralPoint = AUTO, target: GeneralPoint = AUTO, up: GeneralVector = AUTO) -> bool:
        if position == AUTO:
            position = self.position
        if target == AUTO:
            target = self.target
        if up == AUTO:
            up = self.up
        if isinstance(position, tuple):
            position = Point(*position)
        if isinstance(target, tuple):
            target = Point(*target)
        if isinstance(up, tuple):
            up = Vector(*up)
        self.target = target
        self.up = up
        self.position, collide = self.position_refiner(position)
        self.calc_sight()
        return collide

    def calc_sight(self):
        sight = self.target - self.position
        self.theta = sight.theta
        self.phi = sight.phi
    
    def flip(self):
        _, _, coord = get_control_coordinator()
        if self.left_sided or self.right_sided:
            length = self.half_ipd
            self.in_flip = True
            theta = self.theta + pi / 2 if self.left_sided else self.theta - pi / 2
            delta_pos = cos(theta) * length * coord[0] + sin(theta) * length * coord[1]
            delta = Vector(*delta_pos)
            position = delta + self.position
            target = delta * self.concentrate + self.target
            self.in_flip = False
        else:
            position = self.position
            target = self.target
        glPopMatrix()
        glPushMatrix()
        self.calc_sight()
        up = self.up
        gluLookAt(0, 0, 0, target.x - position.x, target.y - position.y, target.z - position.z, up.x, up.y, up.z)

        glRotatef(-self.tilt / pi * 180, *(coord[0] * cos(self.theta) + coord[1] * sin(self.theta)).tolist())
        glTranslatef(-position.x, -position.y, -position.z)
        

    def get_up(self) -> Vector:
        _, _, coord = get_control_coordinator()
        up = cos(self.tilt) * coord[2] + sin(self.tilt) * \
            (cos(self.theta) * coord[0] + sin(self.theta) * coord[1])
        print(up)
        return Vector(*up.tolist())

    def set_position(self, position: GeneralPoint) -> bool:
        theta, phi = self.theta, self.phi
        collide = self.glu_look_at(position=position)
        self.look_at(theta, phi)
        return collide
    
    def look_at(self, theta: float | None = None, phi: float | None = None, tilt: float | None = None, enforce=False):
        if self.suppress_control and not enforce:
            return
        if theta is None:
            theta = self.theta
        else: 
            self.theta = theta
        if phi is None:
            phi = self.phi
        else:
            self.phi = phi
        if tilt is not None:
            self.tilt = tilt
        _, _, coord = get_control_coordinator()
        self.delta_pos = cos(theta) * cos(phi) * coord[0] + sin(theta) * cos(phi) * coord[1] + sin(phi) * coord[2]
        
        target = Vector(*self.delta_pos) + self.position
        self.glu_look_at(target=target)
    
    def move_forward(self, length: float) -> bool:
        return self.move_in_plane(length, 0)
    
    def move_right(self, length: float) -> bool:
        return self.move_in_plane(length, -pi / 2)
    
    def move_up(self, length: float) -> bool:
        if self.suppress_control:
            return
        _, _, coord = get_control_coordinator()
        delta_pos = length * coord[2]
        return self.set_position(Vector(*delta_pos) + self.position)
    
    def move_in_plane(self, length: float, theta: float) -> bool:
        _, _, coord = get_control_coordinator()
        if self.suppress_control:
            return
        theta = self.theta + theta
        delta_pos = cos(theta) * length * coord[0] + sin(theta) * length * coord[1]
        return self.set_position(Vector(*delta_pos) + self.position)
    
    def rotate(self, left: float, up: float):
        if self.suppress_control:
            return
        self.theta += left
        self.phi += up
        if self.phi > HALF_PI:
            self.phi = HALF_PI
        elif self.phi < -HALF_PI:
            self.phi = -HALF_PI
        self.look_at()

    def move_to(self, frames: int, position: GeneralPoint | None = None, 
                theta: float | None = None, phi: float | None = None, suppress_control: bool = True, 
                after: Callable | None = None, report_url: str | None = None):
        if position is None:
            position = self.position
        if theta is None:
            theta = self.theta
        if phi is None:
            phi = self.phi
        if isinstance(position, tuple):
            position = Point(*position)
        if phi > HALF_PI:
            phi = HALF_PI
        elif phi < -HALF_PI:
            phi = -HALF_PI
        while theta < 0:
            theta += 2 * pi
        while self.theta < 0:
            self.theta += 2 * pi
        delta_pos = (position - self.position) / frames
        if abs(theta - self.theta) > pi:
            if theta > self.theta:
                theta -= 2 * pi
            else:
                self.theta -= 2 * pi
        delta_theta = (theta - self.theta) / frames
        delta_phi = (phi - self.phi) / frames
        pos_lst = [self.position + delta_pos * i for i in range(frames)]
        theta_lst = [self.theta + delta_theta * i for i in range(frames)]
        phi_lst = [self.phi + delta_phi * i for i in range(frames)]
        self.suppress_control = suppress_control
        i = 0
        draw = self.render.draw
        draw_without_opengl = self.render.draw_without_opengl
        def new_draw(render: "Render"):
            nonlocal i
            self.set_position(pos_lst[i])
            self.look_at(theta_lst[i], phi_lst[i], enforce=True)
            i += 1
            if render.with_opengl:
                draw(render)
            else:
                draw_without_opengl(render)
            if i == frames:
                self.render.draw = draw
                self.render.draw_without_opengl = draw_without_opengl
                self.calc_sight()
                if after is not None:
                    after()
                if report_url is not None:
                    requests.get(report_url)
                self.suppress_control = False
        self.render.draw = new_draw
        self.render.draw_without_opengl = new_draw
    
    def change_axis(self, in_tube: bool = False, report_url: str | None = None):
        "this method changes up axis to front"
        if self.suppress_control:
            if report_url is not None:
                requests.get(report_url)
            return
        self.calc_sight()
        _, axis, _ = get_control_coordinator()
        if self.theta > pi:
            self.theta -= pi * 2
        elif self.theta < -pi:
            self.theta += pi * 2
        new_phi = HALF_PI
        if -pi / 4 < self.theta < pi / 4:
            new_theta = 0
        elif pi / 4 < self.theta < 3 * pi / 4:
            new_theta = pi / 2
        elif -3 * pi / 4 < self.theta < -pi / 4:
            new_theta = -pi / 2
        else:
            new_theta = pi - 1e-3
        def get_axis(theta: float) -> str:
            if theta > pi:
                theta -= pi * 2
            elif theta < -pi:
                theta += pi * 2
            if -pi / 4 < theta < pi / 4:
                return axis[0]
            elif pi / 4 < theta < 3 * pi / 4:
                return axis[1]
            elif -3 * pi / 4 < theta < -pi / 4:
                return f"{axis[1][0]}{'-' if axis[1][1] == '+' else '+'}"
            else:
                return f"{axis[0][0]}{'-' if axis[0][1] == '+' else '+'}"
        new_axis = [get_axis(self.theta - pi / 2), axis[2], get_axis(self.theta + pi)]
        new_pos = self.position
        if in_tube:
            this = Tube.ALL[Point(int(self.position.x), int(self.position.y), int(self.position.z))]
            front = get_axis(self.theta)
            if front in this.direction:
                if report_url is not None:
                    requests.get(report_url)
                return
            viewer = get_var("GLOBAL_VIEWER")
            delta = viewer.maze.delta
            if front == "x+":
                new_pos = Point(int(self.position.x) + 1 - delta, self.position.y, self.position.z)
            elif front == "x-":
                new_pos = Point(int(self.position.x) + delta, self.position.y, self.position.z)
            elif front == "y+":
                new_pos = Point(self.position.x, int(self.position.y) + 1 - delta, self.position.z)
            elif front == "y-":
                new_pos = Point(self.position.x, int(self.position.y) + delta, self.position.z)
            elif front == "z+":
                new_pos = Point(self.position.x, self.position.y, int(self.position.z) + 1 - delta)
            elif front == "z-":
                new_pos = Point(self.position.x, self.position.y, int(self.position.z) + delta)
        def after(theta=self.theta, phi=self.phi):
            set_control_coordinator(*new_axis, self.render.camera)
            self.render.camera.calc_sight()
            controller = get_var("ArduinoController")
            if controller is not None:
                controller.set_theta(self.render.camera.theta)
                # self.move_to(50, theta=theta, phi=phi)
        
        self.move_to(60, position=new_pos, theta=new_theta, phi=new_phi, after=after, report_url=report_url)
    
    def show_path(self, report_url: str | None = None):
        viewer = get_var("GLOBAL_VIEWER")
        viewer.show_path(self.position)
        if report_url is not None:
            requests.get(report_url)
    
    def hide_path(self, report_url: str | None = None):
        viewer = get_var("GLOBAL_VIEWER")
        viewer.hide_path()
        if report_url is not None:
            requests.get(report_url)
    
    def mark(self, report_url: str | None = None):
        viewer = get_var("GLOBAL_VIEWER")
        viewer.mark()
        if report_url is not None:
            requests.get(report_url)
        

class Render:
    def __init__(self, camera: Camera, size: Tuple[int, int] | None = None, fovy: int = 45, z_near: float = 0.1, 
                 z_far: float = 500.0, after: Callable | None = None, event: Callable | None = None, 
                 sight_len: int = 99999, auto_light: bool = False, g: float = 0.0004, maxspeed: float = 0.08) -> None:
        "`after` is a function that will be run in a thread with param=(self, )"
        set_var("GLOBAL_RENDER", self)
        if size is None:
            user32 = ctypes.windll.user32
            screen_size: Tuple[int, int] = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
            PARSER: ArgumentParser = get_var("PARSER")
            if PARSER.parse_args().left:
                size = screen_size[0] // 2, screen_size[1]
                position = 0, 0 # the position of the window, left top corner
            elif PARSER.parse_args().right:
                size = screen_size[0] // 2, screen_size[1]
                position = screen_size[0] // 2, 0
            else:
                size = screen_size
                position = 0, 0
            self.fullscreen = True
        else:
            self.fullscreen = False
        self.size = size
        self.camera = camera
        camera.render = self
        self.fovy = fovy
        self.z_near = z_near
        self.z_far = z_far
        if after is not None:
            self.after = after
        if event is not None:
            self.event = event
        self.sight_len = sight_len
        self.auto_light = auto_light
        self.g = g
        self.maxspeed = maxspeed
        self.speed = 0.0
        self.position = position
        self.objs = []
        self.with_opengl: bool
        self.animation_tasks: List[Animation] = []
    
    def opengl_init(self):
        self.with_opengl = True
        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{self.position[0]},{self.position[1]}"
        pygame.init()
        self.screen = pygame.display.set_mode(self.size, DOUBLEBUF | OPENGL | NOFRAME)
        gluPerspective(self.fovy, (self.size[0] / self.size[1]), self.z_near, self.z_far)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_NORMALIZE)
        glPushMatrix()
        
    
    def no_opengl_init(self):
        self.with_opengl = False
        pygame.init()
        for font in get_var("CLASS_FONT").ALL:
            font.init_font()
        for text in get_var("CLASS_TEXT").ALL:
            text.init_text()
        fullscreen = get_var("NO_OPENGL_FULLSCREEN")
        self.screen = pygame.display.set_mode(self.size, NOFRAME | (FULLSCREEN if fullscreen else 0))
        self.fuchsia = (255, 0, 128)  # Transparency color
        hwnd = pygame.display.get_wm_info()["window"]
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                               win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.fuchsia), 0, win32con.LWA_COLORKEY)
        def set_topmost():
            while True:
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                sleep(0.05)
        Thread(target=set_topmost).start()
            

    def __call__(self, draw: Callable) -> Callable:
        "register the draw function"
        self.draw = draw
        return draw
    
    def draw(self, func: Callable) -> Callable:
        "you can use a decorator to set draw function\n"
        "the draw function will be run in the main thread with param=(self, ) repeatedly"
        "mostly it's a unused stuff"
        self.draw = func
        return func
    
    def draw_without_opengl(self, func: Callable) -> Callable:
        "you can use a decorator to set draw function\n"
        "the draw function will be run in the main thread with param=(self, ) repeatedly"
        "mostly it's a unused stuff"
        self.draw_without_opengl = func
        return func
    
    def after(self, func: Callable) -> Callable:
        "if you don't set the after function in the __init__ function, you can use a decorator to set it\n"
        "the after function will be run in a thread with param=(self, )"
        self.after = func
        return func
    
    def event(self, func: Callable) -> Callable:
        "if you don't set the after function in the __init__ function, you can use a decorator to set it\n"
        "the event function will be run in the main thread with param=(pygame.event.Event, ) repeatedly"
        self.event = func
        return func

    def mainloop(self):
        if isinstance(self.draw, MethodType): # the user haven't set the draw function
            raise NotImplementedError("You should use the decorator to set the draw function")
        if not isinstance(self.after, MethodType): # the user have set the after function
            self.thread = Thread(target=self.after, args=(self, ))
            self.thread.start()
        else:
            self.thread = None
        self.register_event = not isinstance(self.event, MethodType)
        if get_var("NO_OPENGL"):
            return self.no_opengl_mainloop()
        self.opengl_init()
        if get_var("DISABLE_MOUSE"):
            pygame.mouse.set_visible(False)
        while True:
            for event in pygame.event.get():
                if get_var("CLOSE"):
                    pygame.quit()
                    os._exit(0)
                if self.register_event:
                    self.event(event)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self.draw(self) # Note: it is a static method( or you can see it as a function )
            if self.g and not get_var("WEB_CONTROLLED"):
                self.drop()
            self.camera.flip()
            pygame.display.flip()
    
    def no_opengl_mainloop(self):
        self.no_opengl_init()
        if get_var("DISABLE_MOUSE"):
            pygame.mouse.set_visible(False)
        has_draw = not isinstance(self.draw, MethodType)
        while True:
            for event in pygame.event.get():
                if get_var("CLOSE"):
                    pygame.quit()
                    os._exit(0)
                if self.register_event:
                    self.event(event)
            self.screen.fill(self.fuchsia)  # Transparent background
            if self.g:
                self.drop()
            if self.animation_tasks:
                on_del = []
                for i, task in enumerate(self.animation_tasks):
                    if task.next():
                        on_del.append(i)
                for i in on_del[::-1]:
                    del self.animation_tasks[i]
            if has_draw:
                self.draw_without_opengl(self)
            pygame.display.update()
            sleep(0.001)

    def add_animation(self, animation: Animation):
        self.animation_tasks.append(animation)

    def register(self, obj):
        self.objs.append(obj)
    
    def draw_objs(self):
        if self.auto_light:
            pos = self.camera.position
            pos = Point(int(pos.x), int(pos.y), int(pos.z))
            Tube.reset_brightness_level()
            FloatingBlock.reset_brightness_level()
            Tube.ALL[pos].set_light(get_max_brightness_level(), 
                                    Point(self.camera.position.x - pos.x, self.camera.position.y - pos.y, self.camera.position.z - pos.z))
            
        for obj in self.objs:
            if isinstance(obj, Tube) and obj.brightness_level <= 0:
                continue
            arrow = obj.pos_scaler - self.camera.position
            length = arrow.length
            if length < 2:
                obj.draw()
                continue
            if length < self.sight_len and arrow.dot(self.camera.target - self.camera.position) > -2:
                obj.draw()

    def drop(self):
        self.speed += self.g
        if self.speed > self.maxspeed:
            self.speed = self.maxspeed
        if self.camera.move_up(-self.speed):
            self.speed = 0.0
        
set_var("CLASS_RENDER", Render)