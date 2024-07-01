import os
import sys

ROOT_NAME, _, _ = __name__.partition(".")
ROOT_MODULE = sys.modules[ROOT_NAME]
ROOT_DIR = os.path.dirname(ROOT_MODULE.__file__)
RESOURCE_DIR = os.path.join(ROOT_DIR, "resource")
HISTORY_DIR = os.path.join(RESOURCE_DIR, "history" )

