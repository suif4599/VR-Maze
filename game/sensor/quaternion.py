from enum import Enum
from typing import Union
from math import atan2, pi, asin, acos

class EularOrder(Enum):
    XYZ = 0
    XZY = 1
    YXZ = 2
    YZX = 3
    ZXY = 4
    ZYX = 5

class Quaternion:
    "using n/N in format to normalize the quaternion\n"
    "using v in format to represent the vector part of the quaternion\n"
    "using V in format to represent the unit vector part of the quaternion\n"
    "using e in format to represent the euler angles of the quaternion\n"
    "using E in format to represent the euler angles of the quaternion in degrees\n"
    "using a in format to represent the axis-angle representation of the quaternion\n"
    "using A in format to represent the axis-angle representation of the quaternion in degrees\n"
    "using o in format to represent the orientation of the mpu placing according to the mpu_placing.png\n"
    "using O in format to represent the orientation of the mpu placing according to the mpu_placing.png in degrees\n"
    def __init__(self, w: Union[float, "Quaternion"], x: float = 0.0, y: float = 0.0, z: float = 0.0) -> None:
        if isinstance(w, Quaternion):
            w, x, y, z = w.w, w.x, w.y, w.z
        self.w = float(w)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other: Union[float, "Quaternion"]) -> "Quaternion":
        other = Quaternion(other)
        return Quaternion(self.w + other.w, self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Union[float, "Quaternion"]) -> "Quaternion":
        other = Quaternion(other)
        return Quaternion(self.w - other.w, self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, other: Union[float, "Quaternion"]) -> "Quaternion":
        other = Quaternion(other)
        return Quaternion(self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
                          self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
                          self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
                          self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w)
    
    def __truediv__(self, other: Union[float, "Quaternion"]) -> "Quaternion":
        other = Quaternion(other)
        return self * other.inverse()
    
    def __neg__(self) -> "Quaternion":
        return Quaternion(-self.w, -self.x, -self.y, -self.z)
    
    def __abs__(self) -> float:
        return (self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5
    
    def inverse(self) -> "Quaternion":
        l = self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2
        return Quaternion(self.w / l, -self.x / l, -self.y / l, -self.z / l)
    
    def __str__(self) -> str:
        return f"Quaternion({self.w}, {self.x}, {self.y}, {self.z})"
    
    def __repr__(self) -> str:
        return str(self)
    
    # @property
    # def roll(self) -> float:
    #     norm = self.unit
    #     return atan2(2 * (norm.w * norm.x + norm.y * norm.z), 1 - 2 * (norm.x ** 2 + norm.y ** 2))
    
    # @property
    # def pitch(self) -> float:
    #     norm = self.unit
    #     return asin(2 * (norm.w * norm.y - norm.z * norm.x))
    
    # @property
    # def yaw(self) -> float:
    #     norm = self.unit
    #     return atan2(2 * (norm.w * norm.z + norm.x * norm.y), 1 - 2 * (norm.y ** 2 + norm.z ** 2))
   
    @property
    def roll(self) -> float:
        norm = self.unit
        return atan2(2 * (norm.w * norm.z + norm.x * norm.y), 1 - 2 * (norm.x ** 2 + norm.z ** 2))

    @property
    def pitch(self) -> float:
        norm = self.unit
        return asin(2 * (norm.z * norm.y + norm.w * norm.x))
    
    @property
    def yaw(self) -> float:
        norm = self.unit
        return atan2(2 * (norm.w * norm.y + norm.x * norm.z), 1 - 2 * (norm.x ** 2 + norm.y ** 2))
   
    @property
    def unit(self) -> "Quaternion":
        if hasattr(self, "_unit"):
            return self._unit
        self._unit = self / abs(self)
        return self._unit

    def __format__(self, format_spec: str) -> str:
        if "v" in format_spec:
            format_spec = format_spec.replace("v", "")
            expr = f"QuaternionVector([:{format_spec}], [:{format_spec}], [:{format_spec}])".replace("[", "{").replace("]", "}")
            return expr.format(self.x, self.y, self.z)
        if "V" in format_spec:
            format_spec = format_spec.replace("V", "")
            expr = f"QuaternionUnitVector([:{format_spec}], [:{format_spec}], [:{format_spec}])".replace("[", "{").replace("]", "}")
            l = (self.x ** 2 + self.y ** 2 + self.z ** 2 + 1e-6) ** 0.5
            return expr.format(self.x / l, self.y / l, self.z / l)
        if "e" in format_spec:
            format_spec = format_spec.replace("e", "")
            expr = f"QuaternionEuler([:{format_spec}], [:{format_spec}], [:{format_spec}])".replace("[", "{").replace("]", "}")
            return expr.format(self.roll, self.pitch, self.yaw)
        if "E" in format_spec:
            format_spec = format_spec.replace("E", "")
            expr = f"QuaternionEuler([:{format_spec}], [:{format_spec}], [:{format_spec}])".replace("[", "{").replace("]", "}")
            return expr.format(self.roll / pi * 180, self.pitch / pi * 180, self.yaw / pi * 180)
        if "a" in format_spec:
            format_spec = format_spec.replace("a", "")
            expr = self.__format__("v" + format_spec) + " @ " + f"QuaternionAngle([:{format_spec}])".replace("[", "{").replace("]", "}")
            return expr.format(2 * acos(self.w))
        if "A" in format_spec:
            format_spec = format_spec.replace("A", "")
            expr = self.__format__("V" + format_spec) + " @ " + f"QuaternionAngle([:{format_spec}])".replace("[", "{").replace("]", "}")
            return expr.format(2 * acos(self.w) / pi * 180)
        if "n" in format_spec or "N" in format_spec:
            l = abs(self)
            if l == 0:
                return "Quaternion(0, 0, 0, 0)"
            format_spec = format_spec.replace("n", "").replace("N", "")
        expr = f"Quaternion([:{format_spec}], [:{format_spec}], [:{format_spec}], [:{format_spec}])".replace("[", "{").replace("]", "}")
        return expr.format(self.w, self.x, self.y, self.z)
    
    @property
    def theta(self) -> float:
        "the angle of the quaternion to the y axis"
        return self.yaw
    
    @property
    def phi(self) -> float:
        "the angle of the quaternion to the z axis"
        return self.pitch
    @property
    def psi(self) -> float:
        "the angle of the quaternion to the x axis"
        return self.roll