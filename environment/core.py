from .check import check_environment
import pip
import json
import os
import sys
import io
from typing import List, Dict

STDOUT: io.StringIO = sys.stdout
def print_msg(msg):
    print(f'[Environment]: {msg}', file=STDOUT)

def install_requirements():
    global STDOUT
    STDOUT = sys.stdout
    sys.stdout = io.StringIO()

    check_environment(allow_packge=True)

    print_msg('Installing requirements...')
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.json')
    with open(requirements_path) as f:
        requirements: List[Dict[str, str | List[str]]] = json.load(f)
    for package in requirements:
        name: str = package['name']
        version: str | None = package.get('version', None)
        import_name: str | List[str] | None = package.get('import', None)
        fromlist: List[str] | None = package.get('from', None)
        print_msg(f'Installing {name}...')
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
            print_msg(f'{name} already installed')
            continue
        except ImportError:
            if version:
                pip.main(['install', f'{name}=={version}'])
            else:
                pip.main(['install', name])
    print_msg('All requirements installed')
    sys.stdout = STDOUT