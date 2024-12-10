from serial import Serial
from serial.serialutil import SerialException
from threading import Thread
from time import sleep, time
import re
from typing import Callable, Tuple
from serial.tools.list_ports import comports

class MultiSerial:
    "the type of data should be <name>: <data>\n"
    "leave port 'auto' or 'auto' to await for the first available ports"
    def __init__(self, port: str | Tuple[str] = "auto", baudrate: int | Tuple[int] = 9600, maxfps: int = 200):
        if not isinstance(port, str) and all(p == "auto" for p in port):
            port = self.await_ports(len(port))
        elif port == "auto":
            port = self.await_ports(1)[0]
        if isinstance(port, str):
            port = (port,)
        if isinstance(baudrate, int):
            baudrate = (baudrate,) * len(port)
        self.ports = port
        self.baudrates = baudrate
        try:
            self.serials = tuple(Serial(p, b) for p, b in zip(port, baudrate))
        except SerialException as err:
            raise PortError(err)
        self.delay = 1 / maxfps
        self.callbacks = {}
        self.default_callbacks = []
    
    def register(self, name: str, func: Callable):
        if name == "default":
            self.default_callbacks.append(func)
            return
        if name in self.callbacks:
            raise ValueError(f"{name} is already registered")
        self.callbacks[name] = func
    
    def start(self):
        def after():
            buf_lst = [""] * len(self.serials)
            pattern = re.compile(r"(.*?)Start;(.+?);End;(.*)")
            while 1:
                t = time() + self.delay
                for ind, ser in enumerate(self.serials):
                    if ser.in_waiting:
                        buf_lst[ind] += ser.read_all().decode()
                        match = pattern.search(buf_lst[ind])
                        if not match:
                            continue
                        _, data, buf_lst[ind] = match.groups()
                        match = re.match(r"(\w+): (.+)", data)
                        if match:
                            name, data = match.groups()
                            flag = True
                            if name in self.callbacks:
                                self.callbacks[name](data)
                                flag = False
                            if self.default_callbacks:
                                for callback in self.default_callbacks:
                                    callback(data)
                                flag = False
                            if flag:
                                raise RuntimeError(f"{name} is not registered and no default callback registered")
                        else:
                            raise ValueError(f"invalid data syntax: <{data}>")
                dt = t - time()
                if dt > 0:
                    sleep(dt)
                
        self.thread = Thread(target=after)
        self.thread.start()
    
    def __call__(self, callback: Callable) -> Callable:
        self.register("default", callback)
        return callback
    
    def await_ports(self, num: int) -> Tuple[str]:
        old = comports()
        res: list[str] = []
        print(f"Awaiting for {num} serial port(s)")
        while 1:
            new = comports()
            if len(new) > len(old):
                res.append([port.device for port in new if port not in old][0])
                print(f"Port {res[-1]} is connected")
            old = new
            if len(res) == num:
                return tuple(res)
            sleep(0.1)

class PortError(SerialException):
    pass