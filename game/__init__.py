import sys
import io
STDOUT = sys.stdout
sys.stdout = io.StringIO()
try:
    __import__("pygame")
except ImportError:
    pass
sys.stdout = STDOUT
del STDOUT

from .control import *
from .engine import *
from .maze import *
from .sensor import *
from .animation import *
from .interface import *

def allow_error(sys=sys):
    sys.stderr = STDERR

def suppress_error(sys=sys, io=io):
    sys.stderr = io.StringIO()

del sys
del io

def exit_window():
    from .engine.global_var import set_var
    set_var("CLOSE", True)