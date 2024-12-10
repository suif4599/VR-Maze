from OpenGL.GL import *
from OpenGL.GLU import *
from .base_wrapper import *
import re
from typing import Tuple, List
from .global_var import get_var
import time

class Line:
    def __init__(self, start: GeneralPoint, end: GeneralPoint, color: GeneralColor | None = None):
        if isinstance(start, tuple):
            start = Point(*start)
        if isinstance(end, tuple):
            end = Point(*end)
        if isinstance(color, tuple):
            color = Color(*color)
        self.start = start
        self.end = end
        self.color = color

    def draw(self):
        if self.color is None:
            if self.start.color == self.end.color:
                color = self.start.color
            else:
                raise ValueError("Cannot draw a line with two different colors")
        else:
            color = self.color
        glBegin(GL_LINES)
        glColor3fv((color.r, color.g, color.b))
        glVertex3fv((self.start.x, self.start.y, self.start.z))
        glVertex3fv((self.end.x, self.end.y, self.end.z))
        glEnd()

class Quad:
    def __init__(self, points: Tuple[GeneralPoint, GeneralPoint, GeneralPoint, GeneralPoint], 
                 norm: GeneralVector = AUTO, color: GeneralColor | None = None,
                 texture: Texture | None = None, register: bool = True):
        if isinstance(color, tuple):
            color = Color(*color)
        points = tuple(Point(*p, color) if isinstance(p, tuple) else p for p in points)
        self.points = points
        self.color = color
        self.texture = texture
        if norm == AUTO: # Calculate the normal vector and add a sub-quad with the negative normal vector
            v1 = Vector(points[1].x - points[0].x, points[1].y - points[0].y, points[1].z - points[0].z)
            v2 = Vector(points[2].x - points[0].x, points[2].y - points[0].y, points[2].z - points[0].z)
            v3 = Vector(points[3].x - points[0].x, points[3].y - points[0].y, points[3].z - points[0].z)
            norm = Vector(v1.y * v2.z - v1.z * v2.y, v1.z * v2.x - v1.x * v2.z, v1.x * v2.y - v1.y * v2.x)
            norm = norm.normalize()
            # check if the four points are in the same plane
            if not all(abs(norm.x * vec.x + norm.y * vec.y + norm.z * vec.z) < 1e-4 for vec in (v1, v2, v3)):
                raise ValueError("The four points are not in the same plane")
            self.norm = norm
        else:
            self.norm = norm
        if register:
            get_var("GLOBAL_RENDER").register(self)
            self.pos_scaler = self.points[0] # the render will use it to calculate the position of the quad

    def draw(self):
        if self.color is None:
            if all(point.color == self.points[0].color for point in self.points):
                color = self.points[0].color
            else:
                raise ValueError("Cannot draw a quad with different colors")
        else:
            color = self.color
        has_texture = self.texture is not None
        if has_texture:
            self.texture.enable()
        glBegin(GL_QUADS)
        glNormal3fv((self.norm.x, self.norm.y, self.norm.z))
        glColor3fv((color.r, color.g, color.b))
        if has_texture:
            for point, tex in zip(self.points, self.texture.COORD):
                glTexCoord2fv(tex)
                glVertex3fv((point.x, point.y, point.z))
        else:
            for point in self.points:
                glVertex3fv((point.x, point.y, point.z))
        glEnd()
        if has_texture:
            self.texture.disable()

    def change_color(self, color: GeneralColor):
        if isinstance(color, tuple):
            color = Color(*color)
        self.color = color
    
    def change_texture(self, texture: Texture):
        self.texture = texture

class Text:
    "it can take multiple lines of text\n"
    "it can be shown on one side or two sides\n"
    "it can be formatted with the format method\n"
    "it can diminish some of the text with <diminish=seconds>*</diminish>"
    ALL = []
    def __init__(self, text: str = "", font: Font = CONSOLAS, color: GeneralColor = RED, 
                 line_spacing: float = 1.1, double_side: bool | None = None) -> None:
        if isinstance(color, tuple):
            color = Color(*color)
        self.text = text.strip()
        self.raw_text = text
        self.font = font
        self.color = color
        self.line_spacing = line_spacing
        self.step = int(self.font.size * self.line_spacing)
        if double_side is None:
            self.double_side = get_var("PORT_NUM") == 2
        else:
            self.double_side = double_side
        self.surfaces: List[pygame.Surface]
        self.initialized = False
        Text.ALL.append(self)
        self.time = -1
    
    def divide(self):
        parts: List[Tuple[str, float | None]] = []
        text = self.text
        st = 0
        while True:
            match = re.search(r"<diminish=(?P<duration>[\d\.]+)>(?P<text>.+?)</diminish>", 
                              text, re.DOTALL)
            if match is None:
                if st < len(text):
                    parts.append((text[st:], None))
                break
            t = match.group()
            text = text.replace(t, " " * len(t), 1)
            if st < match.start():
                parts.append((text[st: match.start()], None))
            st = match.end()
            parts.append((match.group("text"), float(match.group("duration"))))
        self.parts = parts
        
    
    def init_text(self, max_len: int = -1):
        if max_len == -1:
            self.surfaces = [self.font.pygame_font.render(
                line, 0, self.color.to_int_tuple()) for line in self.text.split("\n")]
        else:
            self.surfaces = []
            for line in self.text.split("\n"):
                words = line.split(" ")
                while words:
                    ind = 1
                    while ind <= len(words) + 1:
                        if ind > len(words) or len(" ".join(words[: ind])) > max_len:
                            self.surfaces.append(self.font.pygame_font.render(
                                " ".join(words[: ind - 1]), 0, self.color.to_int_tuple()))
                            words = words[ind - 1:]
                            ind = 1
                            if words:
                                words[0] = " " * 4 + words[0]
                            break
                        ind += 1
                
    def format(self, *args, **kwargs):
        self.text = self.raw_text.format(*args, **kwargs)
        self.divide()
        self.initialized = False
    
    def draw(self, render, position: Tuple[int, int] = (10, 10)):
        if self.time == -1:
            self.time = time.time()
        text = ''.join(text for text, duration in self.parts if duration is None \
                       or time.time() - self.time < duration)
        if text != self.text:
            self.text = text
            self.initialized = False
        max_len = int((render.size[0] / 2 - position[0]) / (self.font.size * 0.55)) - 1
        if not self.double_side:
            max_len *= 2
        if not self.initialized:
            self.init_text(max_len)
            self.initialized = True
        hei = range(position[1], position[1] + len(self.surfaces) * self.step, self.step)
        for line, h in zip(self.surfaces, hei):
            render.screen.blit(line, (position[0], h))
            if self.double_side:
                render.screen.blit(line, (position[0] + render.size[0] // 2, h))

set_var("CLASS_TEXT", Text)