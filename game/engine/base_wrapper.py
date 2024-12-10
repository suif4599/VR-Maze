from typing import Tuple
from math import inf, atan, pi
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from .global_var import get_control_coordinator, set_var
import numpy as np
WHITE = (1.0, 1.0, 1.0)
RED = (1.0, 0.3, 0.3)
GREEN = (0.3, 1.0, 0.3)
BLUE = (0.3, 0.3, 1.0)
BLACK = (0.0, 0.0, 0.0)
YELLOW = (1.0, 1.0, 0.3)
CYAN = (0.3, 1.0, 1.0)
MAGENTA = (1.0, 0.3, 1.0)
AUTO = (inf, inf, inf) # inf == inf is True in Python


class Point:
    def __init__(self, x: float, y: float, z: float, color: 'GeneralColor' = WHITE):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        if isinstance(color, tuple):
            color = Color(*color)
        self.color = color

    def __eq__(self, value: 'GeneralPoint') -> bool:
        if isinstance(value, tuple):
            value = Point(*value)
        return self.x == value.x and self.y == value.y and self.z == value.z and self.color == value.color

    def __add__(self, value: 'GeneralVector') -> 'Point':
        if isinstance(value, tuple):
            value = Vector(*value)
        return Point(self.x + value.x, self.y + value.y, self.z + value.z)

    def __sub__(self, value: 'GeneralPoint') -> 'Vector':
        if isinstance(value, tuple):
            value = Point(*value)
        return Vector(self.x - value.x, self.y - value.y, self.z - value.z)
    
    def __str__(self) -> str:
        return f"Point({self.x: .2f}, {self.y: .2f}, {self.z: .2f})"
    
    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))

class Color:
    def __init__(self, r: float, g: float, b: float):
        self.r = float(r)
        self.g = float(g)
        self.b = float(b)

    def __eq__(self, value: 'GeneralColor') -> bool:
        if isinstance(value, tuple):
            value = Color(*value)
        return self.r == value.r and self.g == value.g and self.b == value.b
    
    def __mul__(self, value: float) -> 'Color':
        return Color(self.r * value, self.g * value, self.b * value)
    
    def __rmul__(self, value: float) -> 'Color':
        return Color(self.r * value, self.g * value, self.b * value)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return self.r, self.g, self.b
    
    def to_int_tuple(self) -> Tuple[int, int, int]:
        return int(self.r * 255), int(self.g * 255), int(self.b * 255)

class Vector:
    def __init__(self, x: float, y: float, z: float):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __eq__(self, value: 'GeneralVector') -> bool:
        if isinstance(value, tuple):
            value = Vector(*value)
        return self.x == value.x and self.y == value.y and self.z == value.z

    def __add__(self, value: 'GeneralVector') -> 'Vector':
        if isinstance(value, tuple):
            value = Vector(*value)
        return Vector(self.x + value.x, self.y + value.y, self.z + value.z)

    def __sub__(self, value: 'GeneralVector') -> 'Vector':
        if isinstance(value, tuple):
            value = Vector(*value)
        return Vector(self.x - value.x, self.y - value.y, self.z - value.z)

    def __mul__(self, value: float) -> 'Vector':
        return Vector(self.x * value, self.y * value, self.z * value)
    
    def __rmul__(self, value: float) -> 'Vector':
        return Vector(self.x * value, self.y * value, self.z * value)

    def __neg__(self) -> 'Vector':
        return Vector(-self.x, -self.y, -self.z)
    
    def __truediv__(self, value: float | int) -> 'Vector':
        return Vector(self.x / value, self.y / value, self.z / value)

    def __str__(self) -> str:
        return f"Vector({self.x: .2f}, {self.y: .2f}, {self.z: .2f})"
    
    def __repr__(self) -> str:
        return str(self)
    
    def normalize(self) -> 'Vector':
        length = self.length
        return Vector(self.x / length, self.y / length, self.z / length)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return self.x, self.y, self.z
    
    def dot(self, value: 'GeneralVector') -> float:
        if isinstance(value, tuple):
            value = Vector(*value)
        return self.x * value.x + self.y * value.y + self.z * value.z

    @property
    def length(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    @property
    def theta(self) -> float:
        _, _, coord = get_control_coordinator()
        pos_arr = np.array([self.x, self.y, self.z])
        x = sum(pos_arr[coord[0] == 1]) - sum(pos_arr[coord[0] == -1])
        y = sum(pos_arr[coord[1] == 1]) - sum(pos_arr[coord[1] == -1])
        x = x + (1e-6 if  x > 0 else -1e-6)
        res = atan(y / x)
        if x < 0:
            res += pi
        return res
    
    @property
    def phi(self) -> float:
        _, _, coord = get_control_coordinator()
        pos_arr = np.array([self.x, self.y, self.z])
        x = sum(pos_arr[coord[0] == 1]) - sum(pos_arr[coord[0] == -1])
        y = sum(pos_arr[coord[1] == 1]) - sum(pos_arr[coord[1] == -1])
        z = sum(pos_arr[coord[2] == 1]) - sum(pos_arr[coord[2] == -1])
        return atan(z / ((x ** 2 + y ** 2) ** 0.5 + 1e-6))




class Texture:
    COORD = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    
    def __init__(self, path: str) -> None:
        self.path = path
        if path.split('.')[-1] != 'jpg':
            raise NotImplementedError("Only jpg format is supported now")
        self.surface = pygame.image.load(path)
        self.data = pygame.image.tostring(self.surface, 'RGB', 1)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()

    def enable(self):
        "Enable texture mapping"
        glEnable(GL_TEXTURE_2D)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0, GL_RGB, GL_UNSIGNED_BYTE, self.data)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    def disable(self):
        "Disable texture mapping"
        glDisable(GL_TEXTURE_2D)

class Font:
    "Only in no OpenGL mode"
    ALL = []
    def __init__(self, font_path: str, size: int = 20, bold: bool = False, italic: bool = False, sysfont: bool = False) -> None:
        self.pygame_font: pygame.font.Font
        self.font_path = font_path
        Font.ALL.append(self)
        self.size = size
        self.bold = bold
        self.italic = italic
        self.sysfont = sysfont
    
    def init_font(self):
        if self.sysfont:
            self.pygame_font = pygame.font.SysFont(self.font_path, self.size, self.bold, self.italic)
        else:
            self.pygame_font = pygame.font.Font(self.font_path, self.size, self.bold, self.italic)

    def resize(self, size: int) -> "Font":
        return Font(self.font_path, size, self.bold, self.italic, self.sysfont)

CONSOLAS = Font("consolas", sysfont=True)
set_var("CLASS_FONT", Font)


GeneralPoint = Point | Tuple[int, int, int]
GeneralColor = Color | Tuple[int, int, int]
GeneralVector = Vector | Tuple[int, int, int]