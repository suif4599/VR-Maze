import tkinter.messagebox as msgbox
import traceback
from typing import Callable

class ErrorInterface:
    def __init__(self, exit_func: Callable = lambda: None):
        self.exit_func = exit_func

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None or exc_type is SystemExit:
            return True
        error_name: str = exc_type.__name__
        error_body: str = "\n".join(map(str, exc_val.args))
        error_detail: str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        self.exit_func()
        msgbox.showerror(error_name, f"{error_body}\n\nDetails:\n{error_detail}")
        exit(1)

    def set_exit_func(self, exit_func: Callable):
        self.exit_func = exit_func
