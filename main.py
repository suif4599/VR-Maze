from environment import *
import re
try:
    from game import *
except Exception:
    from argparse import ArgumentParser
    PARSER = ArgumentParser()
import sys


with ErrorInterface(exit_window):
    PARSER.add_argument("-v", "--vr", action="store_true", help="Enable the VR mode")
    PARSER.add_argument("-s", "--serial", type=str, default="(auto,auto)", help="The port of the serial, be single str or tuple of str, use auto to find the port automatically")
    PARSER.add_argument("-b", "--baudrate", type=str, default="57600", help="The baudrate of the serial, be single int or tuple of int")
    PARSER.add_argument("-c", "--check", action="store_true", help="Check the runtime environment")
    PARSER.add_argument("-i", "--install", action="store_true", help="Install the required packages")
    PARSER.add_argument("--ipd", type=float, default=0.01, help="The IPD of the player")
    PARSER.add_argument("--concentrate", type=float, default=0.99, help="The IPD ratio after 1 block")
    PARSER.add_argument("--speed", type=float, default=0.035, help="The speed of the player")
    PARSER.add_argument("--size", type=int, default=15, help="The size of the maze")
    PARSER.add_argument("--collidedistance", type=float, default=0.25, help="The minimum distance between the player and the wall")
    PARSER.add_argument("--maxbrightness", type=int, default=9, help="The maximum brightness level of the screen")
    PARSER.add_argument("--fovy", type=int, default=90, help="The field of view angle of the camera")
    PARSER.add_argument("--allowpath", action="store_true", help="Allow the path to be shown")
    if "-c" in sys.argv or "--check" in sys.argv:
        try:
            check_environment()
        except EnvironmentError as err:
            print_msg(err)
        exit(0)
    if "-i" in sys.argv or "--install" in sys.argv:
        install_requirements()
        exit(0)
    del print_msg


    INSTRUCTION = """<diminish=10>GUIDE:
    Now the IPD is {} block
    {}

    </diminish>Position: {}, {}, {}
    Direction: {}
    """

    args = PARSER.parse_args()
    collidedistance = args.collidedistance
    size = args.size
    speed = args.speed
    port_expr: str = args.serial
    baudrate_expr: str = args.baudrate
    port_match: re.Match | None = re.match(r"^(([(][\w ,]+[)])|([\w ,]+))$", port_expr)
    if port_match is None:
        raise RuntimeError("Port expression is invalid")
    ports: list[str] = re.sub(r"[ ()]+", "", port_match.group()).replace(" ", "").split(",")
    baudrate_match: re.Match | None = re.match(r"^(([(][\d ,]+[)])|([\d ,]+))$", baudrate_expr)
    if baudrate_match is None:
        raise RuntimeError("Baudrate expression is invalid")
    baudrates: list[int] = list(map(int, re.sub(r"[ ()]+", "", baudrate_match.group()).replace(" ", "").split(",")))

    if len(ports) < len(baudrates) or len(ports) > len(baudrates) and len(baudrates) != 1:
        raise RuntimeError("Boudrate must match the port")
    if len(baudrates) == 1:
        baudrates = [baudrates[0] for _ in range(len(ports))]


    if __name__ == "__main__":
        disable_mouse()
        
        maze = Maze(size, size, size, delta=collidedistance, optimizing=True, cells=0.19)
        SUBINSTRUCTION = """The game is controlled by keyboard and mouse
{}<Alt>: mark the your position
<Space>: change your up direction to your forward direction
<Esc>: exit the game""".format(
    '<Ctrl>: show or hide the right path form your position to the target\n' if args.allowpath else '\n')
        if args.vr:
            try:
                controller = ArduinoController(ports, baudrates, 200, speed=speed)
                SUBINSTRUCTION = """The game is controlled by the rocker and mpu6050
<Rocker>: Move the player
<Click>: Mark the player's position
<Double Click>: Change the player's up direction to the forward direction"""
            except Exception as err:
                print(err)
                print("-" * 50)
                print("Use keyboard and mouse instead")
                controller = PCController(speed=speed)
            controller = WebController(controller, (10000, 10111), 10113)
        else:
            controller = PCController(speed=speed)
            controller = WebController(controller, 10000, 10113)
        controller.SHARED_VARIABLES = maze, args
        maze, args = controller.SHARED_VARIABLES

        ipd = args.ipd
        concentrate = args.concentrate
        maxbrightness = args.maxbrightness
        fovy = args.fovy
        allowpath = args.allowpath

        cam = Camera((1.5, 1.5, 1.5), (1.5, 1, 1.5), (0, 0, 1), 
                    position_refiner=maze.position_refiner, 
                    ipd=ipd, concentrate=concentrate)
        render = Render(cam, fovy=fovy, auto_light=True)
        controller.start(render)


        set_max_brightness_level(maxbrightness)
        fp = FlipTexture(render, (Texture("game/texture/light.jpg"), 
                                Texture("game/texture/dark.jpg")),
                        70, 0.0, supress_control=False, web_controller=controller)
        viewer = Viewer(maze, fp, allowpath=allowpath)
        @render.draw
        def draw_maze(render: Render):
            render.draw_objs()


        font = Font("consolas", 30, sysfont=True, bold=True)
        text = Text(INSTRUCTION, font)
        in_cell = False
        @render.draw_without_opengl
        def draw(render: Render):
            global in_cell
            new = maze.in_cell(cam.position)
            if new and not in_cell:
                fp.play()
            in_cell = new

            x1, y1, z1 = int(cam.position.x), int(cam.position.y), int(cam.position.z)
            text.format(ipd, SUBINSTRUCTION, x1, y1, z1, get_axis(cam.theta, cam.phi))
            text.draw(render)


        from math import pi
        def get_axis(theta: float, phi: float) -> str:
            _, axis, _ = get_control_coordinator()
            if phi > pi / 4:
                return axis[2]
            elif phi < -pi / 4:
                return f"{axis[2][0]}{'-' if axis[2][1] == '+' else '+'}"
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

        render.mainloop()
