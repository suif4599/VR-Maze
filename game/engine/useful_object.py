from .base_object import *
from .global_var import get_max_brightness_level
from typing import Tuple, List, Dict, Callable

class Tube:
    all_directions = ('x+', 'x-', 'y+', 'y-', 'z+', 'z-')
    shader = {'x': 0.99, 'y': 0.8, 'z': 1.0}
    ALL: Dict[Point, 'Tube'] = {}
    def __init__(self, position: GeneralPoint, direction: str | Tuple[str, ...], color: GeneralColor = WHITE, 
                 brightness_level: int | None= None, texture: Texture | None = None, 
                 register: bool = True) -> None:
        if isinstance(position, tuple):
            position = Point(*position)
        self.position = position
        Tube.ALL[position] = self
        self.pos_scaler = position
        if isinstance(color, tuple):
            color = Color(*color)
        self.color = color
        if isinstance(direction, str):
            direction = (f"{direction}+", f"{direction}-")
        self.direction = direction
        if brightness_level is None:
            brightness_level = get_max_brightness_level()
        self.brightness_level = brightness_level
        self.texture = texture
        self.faces: List[Quad] = []
        brightness = self.brightness_level / get_max_brightness_level()
        for i in self.all_directions:
            if i in direction:
                continue
            if i == 'x+':
                vertex = ((position.x + 1, position.y, position.z),
                          (position.x + 1, position.y + 1, position.z),
                          (position.x + 1, position.y + 1, position.z + 1),
                          (position.x + 1, position.y, position.z + 1))
            elif i == 'x-':
                vertex = ((position.x, position.y, position.z),
                          (position.x, position.y + 1, position.z),
                          (position.x, position.y + 1, position.z + 1),
                          (position.x, position.y, position.z + 1))
            elif i == 'y+':
                vertex = ((position.x, position.y + 1, position.z),
                          (position.x + 1, position.y + 1, position.z),
                          (position.x + 1, position.y + 1, position.z + 1),
                          (position.x, position.y + 1, position.z + 1))
            elif i == 'y-':
                vertex = ((position.x, position.y, position.z),
                          (position.x + 1, position.y, position.z),
                          (position.x + 1, position.y, position.z + 1),
                          (position.x, position.y, position.z + 1))
            elif i == 'z+':
                vertex = ((position.x, position.y, position.z + 1),
                          (position.x + 1, position.y, position.z + 1),
                          (position.x + 1, position.y + 1, position.z + 1),
                          (position.x, position.y + 1, position.z + 1))
            elif i == 'z-':
                vertex = ((position.x, position.y, position.z),
                          (position.x + 1, position.y, position.z),
                          (position.x + 1, position.y + 1, position.z),
                          (position.x, position.y + 1, position.z))
            self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        if register:
            get_var("GLOBAL_RENDER").register(self) 
    
    def draw(self):
        if not self.brightness_level:
            return
        for face in self.faces:
            face.draw()
    
    def change_color(self, color: GeneralColor, relative_pos: Point | None = None, source_direction: str | None = None):
        if isinstance(color, tuple):
            color = Color(*color)
        self.color = color
        if relative_pos is None and source_direction is None:
            brightness_level = self.brightness_level
        elif relative_pos is None or source_direction is None:
            raise ValueError("Both relative_pos and source_direction should be None or not None")
        else:
            brightness_level = self.brightness_level + 1
            if source_direction == "x+":
                brightness_level -= 1 - relative_pos.x
            elif source_direction == "x-":
                brightness_level -= relative_pos.x
            elif source_direction == "y+":
                brightness_level -= 1 - relative_pos.y
            elif source_direction == "y-":
                brightness_level -= relative_pos.y
            elif source_direction == "z+":
                brightness_level -= 1 - relative_pos.z
            elif source_direction == "z-":
                brightness_level -= relative_pos.z
            elif source_direction == 'center':
                brightness_level -= 1
            else:
                raise ValueError("source_direction should be one of 'x+', 'x-', 'y+', 'y-', 'z+', 'z-', 'center'")
        color = color * (brightness_level / get_max_brightness_level())
        for face in self.faces:
            face.change_color(color)
    
    @classmethod
    def reset_brightness_level(cls):
        for tube in cls.ALL.values():
            tube.brightness_level = 0
    
    def set_light(self, level: int, relative_pos: Point = Point(0.5, 0.5, 0.5), source_direction: str = 'center'):
        self.brightness_level = level
        if not level:
            return
        for direction in self.direction:
            if direction == 'x+':
                pos = Point(self.position.x + 1, self.position.y, self.position.z)
            elif direction == 'x-':
                pos = Point(self.position.x - 1, self.position.y, self.position.z)
            elif direction == 'y+':
                pos = Point(self.position.x, self.position.y + 1, self.position.z)
            elif direction == 'y-':
                pos = Point(self.position.x, self.position.y - 1, self.position.z)
            elif direction == 'z+':
                pos = Point(self.position.x, self.position.y, self.position.z + 1)
            elif direction == 'z-':
                pos = Point(self.position.x, self.position.y, self.position.z - 1)
            if pos in self.ALL and self.ALL[pos].brightness_level < level - 1:
                self.ALL[pos].set_light(level - 1, relative_pos, direction)
        self.change_color(self.color, relative_pos, source_direction)
        if self.pos_scaler in FloatingBlock.ALL:
            FloatingBlock.ALL[self.pos_scaler].set_light(level, relative_pos, source_direction)

    def change_texture(self, texture: Texture):
        self.texture = texture
        for face in self.faces:
            face.change_texture(texture)



class FloatingBlock(Tube):
    ALL: Dict[Point, 'FloatingBlock'] = {}
    def __init__(self, position: GeneralPoint, color: GeneralColor = WHITE, 
                 brightness_level: int | None= None, texture: Texture | None = None, 
                 register: bool = True, collide: bool = True, hide: bool = False) -> None:
        if isinstance(position, tuple):
            position = Point(*position)
        self.position = position
        FloatingBlock.ALL[position] = self
        self.pos_scaler = position
        if isinstance(color, tuple):
            color = Color(*color)
        self.color = color
        if brightness_level is None:
            brightness_level = get_max_brightness_level()
        self.brightness_level = brightness_level
        self.texture = texture
        self.faces: List[Quad] = []
        brightness = self.brightness_level / get_max_brightness_level()
        self.collide = collide
        self.hidden: bool
        self.change_maze_func: Callable | None = None
        if hide:
            self.hide()
        else:
            self.show()
        vertex = ((position.x + 1, position.y, position.z),
                  (position.x + 1, position.y + 1, position.z),
                  (position.x + 1, position.y + 1, position.z + 1),
                  (position.x + 1, position.y, position.z + 1))
        self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        vertex = ((position.x, position.y, position.z),
                  (position.x, position.y + 1, position.z),
                  (position.x, position.y + 1, position.z + 1),
                  (position.x, position.y, position.z + 1))
        self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        vertex = ((position.x, position.y + 1, position.z),
                  (position.x + 1, position.y + 1, position.z),
                  (position.x + 1, position.y + 1, position.z + 1),
                  (position.x, position.y + 1, position.z + 1))
        self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        vertex = ((position.x, position.y, position.z),
                  (position.x + 1, position.y, position.z),
                  (position.x + 1, position.y, position.z + 1),
                  (position.x, position.y, position.z + 1))
        self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        vertex = ((position.x, position.y, position.z),
                  (position.x + 1, position.y, position.z),
                  (position.x + 1, position.y + 1, position.z),
                  (position.x, position.y + 1, position.z))
        self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        vertex = ((position.x, position.y, position.z + 1),
                  (position.x + 1, position.y, position.z + 1),
                  (position.x + 1, position.y + 1, position.z + 1),
                  (position.x, position.y + 1, position.z + 1))
        self.faces.append(Quad(vertex, color=color * brightness, texture=texture, register=not register))
        if register:
            get_var("GLOBAL_RENDER").register(self) 
    
    def set_light(self, level: int, relative_pos: Point = Point(0.5, 0.5, 0.5), source_direction: str = 'center'):
        self.brightness_level = level
        if not level:
            return
        self.change_color(self.color, relative_pos, source_direction)

    def draw(self):
        if not self.brightness_level or self.hidden:
            return
        # self.set_light(get_max_brightness_level())
        for face in self.faces:
            face.draw()

    def show(self):
        self.hidden = False
        if self.collide:
            x, y, z = int(self.pos_scaler.x), int(self.pos_scaler.y), int(self.pos_scaler.z)
            self.change_maze(x, y, z, 0)
            pos = get_var("GLOBAL_RENDER").camera.position
            if int(pos.x) == x and int(pos.y) == y and int(pos.z) == z:
                maze = get_var("GLOBAL_VIEWER").maze.maze
                if maze[x + 1, y, z]:
                    get_var("WEBCONTROLLER").set_position((x + 1, y, z))
                elif maze[x - 1, y, z]:
                    get_var("WEBCONTROLLER").set_position((x - 1, y, z))
                elif maze[x, y + 1, z]:
                    get_var("WEBCONTROLLER").set_position((x, y + 1, z))
                elif maze[x, y - 1, z]:
                    get_var("WEBCONTROLLER").set_position((x, y - 1, z))
                elif maze[x, y, z + 1]:
                    get_var("WEBCONTROLLER").set_position((x, y, z + 1))
                elif maze[x, y, z - 1]:
                    get_var("WEBCONTROLLER").set_position((x, y, z - 1))

    def hide(self):
        self.hidden = True
        if self.collide:
            self.change_maze(int(self.pos_scaler.x), int(self.pos_scaler.y), int(self.pos_scaler.z), 1)

    def change_maze(self, x: int, y: int, z: int, value: int):
        get_var("GLOBAL_VIEWER").maze.maze[x, y, z] = value



