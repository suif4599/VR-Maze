import random
import numpy as np
from ..engine import Point, GeneralPoint
from ..engine.global_var import get_var
from math import inf
from typing import Tuple, Dict, List

class Maze:
    'one is path, zero is wall'
    def __init__(self, rows: int, cols: int, height: int, delta: float = 0.2, optimizing: bool = False,
                 cells: int | float = 0.01) -> None:
        "if cell is int then it is the number of cells, if it is float then it is the density of cells"
        if get_var("WEB_CONTROLLED") and optimizing:
            return
        self.rows = rows
        self.cols = cols
        self.height = height
        self.delta = delta
        self.cell_num = int(cells) if isinstance(cells, int) else int(rows * cols * height * cells)
        self.generate_maze()
        self.solute()

    def generate_maze(self): # from web, i extend it to 3d
        num_rows = self.rows
        num_cols = self.cols
        num_h = self.height
        M = np.zeros((num_rows, num_cols, num_h, 7), dtype=np.uint8)
        # The array M is going to hold the array information for each cell.
        # The first four coordinates tell if walls exist on those sides
        # and the fifth indicates if the cell has been visited in the search.
        # M(LEFT, UP, RIGHT, DOWN, FRONT, BACK, CHECK_IF_VISITED)

        possibility = [(0, 0, 0)]

        while possibility:
            # random choose a candidate cell from the cell set histroy
            r, c, t = random.choice(possibility)
            M[r, c, t, 6] = 1  # designate this location as visited

            possibility.remove((r, c, t))
            check = []
            # If the randomly chosen cell has multiple edges
            # that connect it to the existing self.
            if c > 0:  # the visit state of left cell (for example)
                if M[r, c - 1, t, 6] == 1:  # If this cell was visited,
                    check.append("L")  # it can be choiced as direction.
                elif M[r, c - 1, t, 6] == 0:  # else if it has not been visited...
                    possibility.append((r, c - 1, t))
                    M[r, c - 1, t, 6] = 2
            if r > 0:  # the visit state of up cell
                if M[r - 1, c, t, 6] == 1:
                    check.append("U")
                elif M[r - 1, c, t, 6] == 0:
                    possibility.append((r - 1, c, t))
                    M[r - 1, c, t, 6] = 2
            if t > 0: # the visit state of front cell
                if M[r, c, t - 1, 6] == 1:
                    check.append("F")
                elif M[r, c, t - 1, 6] == 0:
                    possibility.append((r, c, t - 1))
                    M[r, c, t - 1, 6] = 2
            if c < num_cols - 1:  # the visit state of right cell
                if M[r, c + 1, t, 6] == 1:
                    check.append("R")
                elif M[r, c + 1, t, 6] == 0:
                    possibility.append((r, c + 1, t))
                    M[r, c + 1, t, 6] = 2
            if r < num_rows - 1:  # the visit state of down cell
                if M[r + 1, c, t, 6] == 1:
                    check.append("D")
                elif M[r + 1, c, t, 6] == 0:
                    possibility.append((r + 1, c, t))
                    M[r + 1, c, t, 6] = 2
            if t < num_h - 1:  # the visit state of back cell
                if M[r, c, t + 1, 6] == 1:
                    check.append("B")
                elif M[r, c, t + 1, 6] == 0:
                    possibility.append((r, c, t + 1))
                    M[r, c, t + 1, 6] = 2

            # Select one of these edges as direction at random,
            # and break the walls between these two cells.
            if len(check):
                move_direction = random.choice(check)  # Select a direction
                # Break the walls.
                if move_direction == "L":
                    M[r, c, t, 0] = 1
                    c = c - 1
                    M[r, c, t, 2] = 1
                if move_direction == "U":
                    M[r, c, t, 1] = 1
                    r = r - 1
                    M[r, c, t, 3] = 1
                if move_direction == "R":
                    M[r, c, t, 2] = 1
                    c = c + 1
                    M[r, c, t, 0] = 1
                if move_direction == "D":
                    M[r, c, t, 3] = 1
                    r = r + 1
                    M[r, c, t, 1] = 1
                if move_direction == "F":
                    M[r, c, t, 4] = 1
                    t = t - 1
                    M[r, c, t, 5] = 1
                if move_direction == "B":
                    M[r, c, t, 5] = 1
                    t = t + 1
                    M[r, c, t, 4] = 1

        # generate the maze into 2d array without display
        maze = np.zeros((num_rows * 2 + 1, num_cols * 2 + 1, num_h * 2 + 1), dtype=np.uint8)
        for row in range(num_rows):
            for col in range(num_cols):
                for height in range(num_h):
                    maze[row * 2 + 1, col * 2 + 1, height * 2 + 1] = 1
                    if M[row, col, height, 0] == 1:
                        maze[row * 2 + 1, col * 2, height * 2 + 1] = 1
                    if M[row, col, height, 1] == 1:
                        maze[row * 2, col * 2 + 1, height * 2 + 1] = 1
                    if M[row, col, height, 2] == 1:
                        maze[row * 2 + 1, col * 2 + 2, height * 2 + 1] = 1
                    if M[row, col, height, 3] == 1:
                        maze[row * 2 + 2, col * 2 + 1, height * 2 + 1] = 1
                    if M[row, col, height, 4] == 1:
                        maze[row * 2 + 1, col * 2 + 1, height * 2] = 1
                    if M[row, col, height, 5] == 1:
                        maze[row * 2 + 1, col * 2 + 1, height * 2 + 2] = 1
        self.maze = maze
        self.generate_cell()

    def generate_cell(self):
        cell_pos = [(-1, -1, -1)]
        self.cells: Dict[Tuple[int, int, int], int] = {} # Dict[Position, Size]
        for i in range(self.cell_num):
            x, y, z = cell_pos[0]
            cnt = 1
            while min(abs(x - c[0]) + abs(y - c[1]) + abs(z - c[2]) for c in cell_pos) <= 6:
                x = random.randint(0, self.rows - 3)
                y = random.randint(0, self.cols - 3)
                z = random.randint(0, self.height - 3)
                cnt += 1
                if cnt > 100:
                    break
            else: # run if there's no break
                cell_pos.append((x, y, z))
                size = 3
                self.cells[(x, y, z)] = size
                self.maze[x * 2 + 1: x * 2 + size + 1, y * 2 + 1: y * 2 + size + 1, z * 2 + 1: z * 2 + size + 1] = 1
        self.divide_maze()
        self.bordered_part_num = self.gen_floating_blocks()

    def in_cell(self, position: Point) -> bool:
        for pos, size in self.cells.items():
            pos = Point(pos[0] * 2 + 1, pos[1] * 2 + 1, pos[2] * 2 + 1)
            pos2: Point = pos + (size, ) * 3
            if pos.x <= position.x <= pos2.x and pos.y <= position.y <= pos2.y and pos.z <= position.z <= pos2.z:
                return True
        return False

    def position_refiner(self, position: Point, collide: bool = False) -> Tuple[GeneralPoint, bool]:
        delta = self.delta
        if not self.maze[int(position.x + delta), int(position.y), int(position.z)]: # is wall
            return self.position_refiner(Point(int(position.x + delta) - delta * 1.01, position.y, position.z), True)
        if not self.maze[int(position.x - delta), int(position.y), int(position.z)]:
            return self.position_refiner(Point(int(position.x) + delta  * 1.01, position.y, position.z), True)
        if not self.maze[int(position.x), int(position.y + delta), int(position.z)]:
            return self.position_refiner(Point(position.x, int(position.y + delta) - delta * 1.01, position.z), True)
        if not self.maze[int(position.x), int(position.y - delta), int(position.z)]:
            return self.position_refiner(Point(position.x, int(position.y) + delta * 1.01, position.z), True)
        if not self.maze[int(position.x), int(position.y), int(position.z + delta)]:
            return self.position_refiner(Point(position.x, position.y, int(position.z + delta) - delta * 1.01), True)
        if not self.maze[int(position.x), int(position.y), int(position.z - delta)]:
            return self.position_refiner(Point(position.x, position.y, int(position.z) + delta * 1.01), True)
        return position, collide

    def solute(self) -> np.ndarray:
        if hasattr(self, "solution"):
            return self.solution
        solution = np.zeros((self.rows * 2 + 1, self.cols * 2 + 1, self.height * 2 + 1), dtype=np.int32)
        solution[self.maze == 0] = -1
        available = [(self.rows * 2 - 1, self.cols * 2 - 1, self.height * 2 - 1, 1)]
        # visited path: > 0
        # unvisited path: 0
        # wall: -1
        while available:
            x, y, z, d = available.pop()
            if solution[x, y, z]: # if the cell is visited or wall
                continue
            solution[x, y, z] = d
            if solution[x + 1, y, z] == 0: # if the cell is a unvisited path
                solution[x + 1, y, z] = d + 1
                available.append((x + 2, y, z, d + 2))
            if solution[x - 1, y, z] == 0:
                solution[x - 1, y, z] = d + 1
                available.append((x - 2, y, z, d + 2))
            if solution[x, y + 1, z] == 0:
                solution[x, y + 1, z] = d + 1
                available.append((x, y + 2, z, d + 2))
            if solution[x, y - 1, z] == 0:
                solution[x, y - 1, z] = d + 1
                available.append((x, y - 2, z, d + 2))
            if solution[x, y, z + 1] == 0:
                solution[x, y, z + 1] = d + 1
                available.append((x, y, z + 2, d + 2))
            if solution[x, y, z - 1] == 0:
                solution[x, y, z - 1] = d + 1
                available.append((x, y, z - 2, d + 2))
        self.solution = solution
        return solution
    
    def next_path(self, position: GeneralPoint) -> Point:
        if isinstance(position, tuple):
            position = Point(*position)
        x, y, z = int(position.x), int(position.y), int(position.z)
        solution = self.solution
        xp = solution[x + 1, y, z] if solution[x + 1, y, z] > 0 else inf 
        xn = solution[x - 1, y, z] if solution[x - 1, y, z] > 0 else inf
        yp = solution[x, y + 1, z] if solution[x, y + 1, z] > 0 else inf
        yn = solution[x, y - 1, z] if solution[x, y - 1, z] > 0 else inf
        zp = solution[x, y, z + 1] if solution[x, y, z + 1] > 0 else inf
        zn = solution[x, y, z - 1] if solution[x, y, z - 1] > 0 else inf
        m = min(xp, xn, yp, yn, zp, zn)
        if xp == m:
            return Point(x + 1, y, z)
        if xn == m:
            return Point(x - 1, y, z)
        if yp == m:
            return Point(x, y + 1, z)
        if yn == m:
            return Point(x, y - 1, z)
        if zp == m:
            return Point(x, y, z + 1)
        if zn == m:
            return Point(x, y, z - 1)
        
    def divide_maze(self):
        "this method sets self.maze_part and returns the num of parts"
        # 0 in wall, -1 is unvisted, -2 is cell, -3 is floating block, positive integer is the index of the maze
        maze_cp = self.maze.astype(np.int32)
        for (x, y, z), size in self.cells.items():
            maze_cp[x * 2 + 1: x * 2 + size + 1, y * 2 + 1: y * 2 + size + 1, z * 2 + 1: z * 2 + size + 1] = -2
        maze_cp[maze_cp == 1] = -1
        maze: Dict[Tuple[int, int, int], int] = {(x, y, z): maze_cp[x, y, z] for x in range(2 * self.rows + 1) 
                                                 for y in range(2 * self.cols + 1) for z in range(2 * self.height + 1)}
        index = 0
        while True:
            for (x, y, z), state in maze.items():
                if state == -1:
                    index += 1
                    available = [(x, y, z)]
                    while available:
                        x, y, z = available.pop(0)
                        maze[(x, y, z)] = index
                        if maze[(x + 1, y, z)] == -1:
                            available.append((x + 1, y, z))
                        if maze[(x - 1, y, z)] == -1:
                            available.append((x - 1, y, z))
                        if maze[(x, y + 1, z)] == -1:
                            available.append((x, y + 1, z))
                        if maze[(x, y - 1, z)] == -1:
                            available.append((x, y - 1, z))
                        if maze[(x, y, z + 1)] == -1:
                            available.append((x, y, z + 1))
                        if maze[(x, y, z - 1)] == -1:
                            available.append((x, y, z - 1))
                    break
            else:
                break
        self.maze_part = maze
        self.part_num = index
        return index

    def select_from_index(self, index: int) -> Tuple[Tuple[int, int, int], List[Tuple[int, int, int]]] | None:
        "this method returns a random position from the index and guarantee that the position has at least two neighbors\n"
        "it returns <pos>, <neighbors> if it is found, else None"
        cnt = 0
        while True:
            cnt += 1
            pos = random.choice(tuple((x, y, z) for (x, y, z), i in self.maze_part.items() if i == index))
            directions = [[pos[0] + 1, pos[1], pos[2]], [pos[0] - 1, pos[1], pos[2]], [pos[0], pos[1] + 1, pos[2]],
                          [pos[0], pos[1] - 1, pos[2]], [pos[0], pos[1], pos[2] + 1], [pos[0], pos[1], pos[2] - 1]]
            neighbors = [(x, y, z) for x, y, z in directions if self.maze_part[(x, y, z)] == index]
            if len(neighbors) >= 2:
                return pos, neighbors
            if cnt > 100:
                return None

    def gen_floating_blocks(self, num: int = 2) -> int:
        self.floating_block: List[List[Tuple[int, int, int]]] = [[] for _ in range(num)]
        cnt = self.part_num + 1
        type_ = 0
        for ind in range(1, self.part_num + 1):
            available: List[int] = [ind]
            re_calc: Dict[int, int] = {}
            while available:
                ind = available.pop(0)
                if len([0 for _, i in self.maze_part.items() if i == ind]) < 5 or re_calc.get(ind, 0) > 2000:
                    continue
                pos = self.select_from_index(ind)
                if pos is None:
                    continue
                pos, neighbors = pos
                self.maze_part[pos] = -3 # floating block
                flags: List[int] = []
                changed: List[Tuple[int, int, int]] = []
                for neighbor in neighbors:
                    current = [neighbor]
                    flags.append(0)
                    while current:
                        x, y, z = current.pop(0)
                        if self.maze_part[(x, y, z)] == ind:
                            self.maze_part[(x, y, z)] = cnt
                            changed.append((x, y, z))
                            if self.maze_part[(x + 1, y, z)] == ind:
                                current.append((x + 1, y, z))
                            if self.maze_part[(x - 1, y, z)] == ind:
                                current.append((x - 1, y, z))
                            if self.maze_part[(x, y + 1, z)] == ind:
                                current.append((x, y + 1, z))
                            if self.maze_part[(x, y - 1, z)] == ind:
                                current.append((x, y - 1, z))
                            if self.maze_part[(x, y, z + 1)] == ind:
                                current.append((x, y, z + 1))
                            if self.maze_part[(x, y, z - 1)] == ind:
                                current.append((x, y, z - 1))
                        elif self.maze_part[(x, y, z)] == -2: # cell
                            flags[-1] |= 1
                        elif self.maze_part[(x, y, z)] == -3: # floating block
                            flags[-1] += 64
                    cnt += 1
                if any(flag % 64 == 0 and flag >= 128 for flag in flags):
                    self.maze_part[pos] = ind
                    for x, y, z in changed:
                        self.maze_part[(x, y, z)] = ind
                    if ind not in re_calc:
                        re_calc[ind] = 0
                    re_calc[ind] += 1
                    continue
                for neighbor, flag in zip(neighbors, flags):
                    if flag & 1:
                        available.append(self.maze_part[neighbor])
                self.floating_block[type_].append(pos)
                type_ = (type_ + 1) % num
        available = [(1, 1, 1)]
        remove_lst = []
        while available:
            x, y, z = available.pop(0)
            if self.maze_part[(x, y, z)] == -3:
                remove_lst.append((x, y, z))
            if self.maze_part[(x + 1, y, z)] in (-3, -1):
                available.append((x + 1, y, z))
            if self.maze_part[(x - 1, y, z)] in (-3, -1):
                available.append((x - 1, y, z))
            if self.maze_part[(x, y + 1, z)] in (-3, -1):
                available.append((x, y + 1, z))
            if self.maze_part[(x, y - 1, z)] in (-3, -1):
                available.append((x, y - 1, z))
            if self.maze_part[(x, y, z + 1)] in (-3, -1):
                available.append((x, y, z + 1))
            if self.maze_part[(x, y, z - 1)] in (-3, -1):
                available.append((x, y, z - 1))
        for pos in remove_lst:
            for i in range(num):
                for j in range(len(self.floating_block[i]) - 1, -1, -1):
                    if self.floating_block[i][j] == pos:
                        self.floating_block[i].pop(j)
                        break
            self.maze_part[pos] = -1
        return len([1 for i in self.floating_block for j in i])
