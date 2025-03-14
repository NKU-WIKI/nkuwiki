import time

import pip
from pip._internal import main as pipmain

from infra.deploy.app import logger


def install(package):
    pipmain(["install", package])


def install_requirements(file):
    pipmain(["install", "-r", file, "--upgrade"])


def check_dulwich():
    needwait = False
    for i in range(2):
        if needwait:
            time.sleep(3)
            needwait = False
        try:
            import dulwich

            return
        except ImportError:
            try:
                install("dulwich")
            except:
                needwait = True
    try:
        import dulwich
    except ImportError:
        raise ImportError("Unable to import dulwich")
