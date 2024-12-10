from .maze3d import Maze
from ..engine import *
from ..engine.global_var import set_var, get_var
from typing import Dict, List
from ..animation import FlipTexture


class Viewer:
    'one is path, zero is wall'
    EXISTS = False
    def __init__(self, maze: Maze, flip_texture: FlipTexture, allowpath: bool = True) -> None:
        if Viewer.EXISTS:
            raise RuntimeError("Viewer already exists")
        Viewer.EXISTS = True
        set_var("GLOBAL_VIEWER", self)
        self.rows = maze.rows
        self.cols = maze.cols
        self.texture = flip_texture.textures[0]
        self.flip_texture = flip_texture
        self.maze = maze
        self.height = maze.height
        self.tubes: Dict[GeneralPoint, Tube] = {}
        self.floating_blocks: Dict[Texture, List[FloatingBlock]] = {}
        self.allowpath = allowpath
        self.register()
        
    def register(self):
        for i in range(1, self.rows * 2):
            for j in range(1, self.cols * 2):
                for k in range(1, self.height * 2):
                    if self.maze.maze[i, j, k]:
                        available: List[str] = []
                        if self.maze.maze[i - 1, j, k]:
                            available.append('x-')
                        if self.maze.maze[i + 1, j, k]:
                            available.append('x+')
                        if self.maze.maze[i, j - 1, k]:
                            available.append('y-')
                        if self.maze.maze[i, j + 1, k]:
                            available.append('y+')
                        if self.maze.maze[i, j, k - 1]:
                            available.append('z-')
                        if self.maze.maze[i, j, k + 1]:
                            available.append('z+')
                        self.tubes[(i, j, k)] = Tube((i, j, k), available, texture=self.texture)
        self.tubes[(1, 1, 1)].change_color((1.0, 0.7, 0.7))
        self.tubes[(2 * self.rows - 1, 2 * self.cols - 1, 2 * self.height - 1)].change_color((0.7, 1.0, 0.7))
        for block_lst, texture in zip(self.maze.floating_block, self.flip_texture.textures):
            self.floating_blocks[texture] = []
            for block in block_lst:
                self.floating_blocks[texture].append(FloatingBlock(block, texture=texture, collide=True, hide=False))
        for blk in self.floating_blocks[self.texture]:
            blk.hide()

    def draw(self):
        for tube in self.tubes.values():
            tube.draw()
    
    def show_path(self, pos: Point = Point(1, 1, 1)):
        if not self.allowpath:
            return
        self.maze.solute()
        # pos = Point(1, 1, 1)
        x, y, z = int(pos.x), int(pos.y), int(pos.z)
        d = self.maze.solution[x, y, z]
        self.tubes[(x, y, z)].change_color((0.7, 0.7, 1.0))
        self.tubes[(1, 1, 1)].change_color((1.0, 0.7, 0.7))
        self.tubes[(2 * self.rows - 1, 2 * self.cols - 1, 2 * self.height - 1)].change_color((0.7, 1.0, 0.7))
        while d > 2:
            pos = self.maze.next_path(pos)
            x, y, z = int(pos.x), int(pos.y), int(pos.z)
            self.tubes[(x, y, z)].change_color((0.7, 0.7, 1.0))
            d = self.maze.solution[x, y, z]

    def hide_path(self):
        for tube in self.tubes.values():
            tube.change_color((1.0, 1.0, 1.0))
        self.tubes[(1, 1, 1)].change_color((1.0, 0.7, 0.7))
        self.tubes[(2 * self.rows - 1, 2 * self.cols - 1, 2 * self.height - 1)].change_color((0.7, 1.0, 0.7))
    
    def mark(self):
        render = get_var("GLOBAL_RENDER")
        pos = render.camera.position
        tube = self.tubes[(int(pos.x), int(pos.y), int(pos.z))]
        if hasattr(tube, "old_color"):
            tube.change_color(tube.old_color)
            del tube.old_color
            return
        tube.old_color = tube.color
        tube.change_color((1.0, 1.0, 0.7))

    def change_texture(self, texture: Texture):
        for tube in self.tubes.values():
            tube.change_texture(texture)
        for block in self.floating_blocks[self.texture]:
            block.show()
        self.texture = texture
        for block in self.floating_blocks[texture]:
            block.hide()
