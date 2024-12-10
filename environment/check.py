import os
import json
import io
import sys
from typing import List, Dict

STDOUT: io.StringIO = sys.stdout
def print_msg(msg):
    print(f'[Environment]: {msg}', file=STDOUT)

def check_environment(allow_packge: bool = False):
    global STDOUT
    STDOUT = sys.stdout
    sys.stdout = io.StringIO()
    print_msg('Checking environment...')
    # pip check
    try:
        import pip
    except ImportError:
        raise EnvironmentError('pip not found, please install pip manually')

    # platform check
    if sys.platform != 'win32':
        raise EnvironmentError('This game is only for Windows, please switch to Windows')

    # package check
    if not allow_packge:
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.json')
        with open(requirements_path) as f:
            requirements: List[Dict[str, str | List[str]]] = json.load(f)
        for package in requirements:
            name: str = package['name']
            import_name: str | List[str] | None = package.get('import', None)
            fromlist: List[str] | None = package.get('from', None)
            try:
                if import_name is not None:
                    if import_name:
                        if not isinstance(import_name, list):
                            import_name = [import_name]
                        for i in import_name:
                            if fromlist:
                                __import__(i, fromlist=fromlist)
                            else:
                                __import__(i)
                else:
                    __import__(name)
                continue
            except ImportError:
                raise EnvironmentError(f'Package <{name}> not found, run with -i or --install to install requirements')
    print_msg('Environment checked')
    sys.stdout = STDOUT