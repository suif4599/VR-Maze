from .multi_serial import MultiSerial
from .quaternion import Quaternion
import re
from math import pi

class MPU:
    "a class that represents a MPU\n"
    "Note: the data of the MPU are in range [-1, 1]\n"
    "when a callback is registered, the callback will be called when the MPU6050 is updated and be presented with self\n"
    def __init__(self, ser: MultiSerial, strict: bool = True) -> None:
        self.ser = ser
        self.ser.register('MPU', self.callback)
        self.q = Quaternion(1, 0, 0, 0)
        self.callbacks = []
        self.strict = strict
        self.delta_theta = 0
    
    def callback(self, data: str) -> None:
        match = re.match(r"([-]?[0-9\.]+), ([-]?[0-9\.]+), ([-]?[0-9\.]+), ([-]?[0-9\.]+)", data)
        if match:
            self.q = Quaternion(*map(lambda x: float(x) * pi, match.groups()))
            for callback in self.callbacks:
                callback(self)
        else:
            if self.strict:
                raise ValueError(f"invalid data: {data}")

    @property
    def theta(self) -> float:
        "the angle of the MPU in xOy plane"
        res = self.q.theta + self.delta_theta
        if res > pi:
            return res - 2 * pi
        if res < -pi:
            return res + 2 * pi
        return res
    
    @property
    def phi(self) -> float:
        "the angle of the MPU to the z axis"
        return -self.q.phi
    
    @property
    def tilt(self) -> float:
        "the tilt of the MPU"
        return self.q.psi
        

    def register(self, func) -> None:
        self.callbacks.append(func)

    def __call__(self, callback) -> None:
        self.register(callback)
        return callback
    
    def set_theta(self, theta: float) -> None:
        self.delta_theta = theta - self.q.theta
