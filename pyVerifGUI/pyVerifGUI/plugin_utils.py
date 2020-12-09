###############################################################################
# @file pyVerifGUI/plugin_utils.py
# @package pyVerifGUI.plugin_utils
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Utilities common for the task and tab plugin systems.
##############################################################################
from typing import Callable, Any, List
from types import ModuleType
from pathlib import Path
import importlib
import inspect
import sys
import os

def _import_file(path: Path, existing_modules: List[str], verify: Callable):
    """Local file importing function. Used for DRY, don't use externally"""

    if path.name == "__init__.py" or path.suffix != ".py":
        return None

    if path.stem in existing_modules:
        print(f"ERROR - plugin found at {path} has a conflicting name")
        sys.exit(1)

    if path.stem in sys.modules:
        del sys.modules[path.stem]

    mod = importlib.import_module(path.stem)
    for cls in inspect.getmembers(mod, inspect.isclass):
        if verify(cls[1]):
            return cls[1], cls[0]

def import_plugins(paths: List[os.PathLike], verify: Callable[[Any], bool]) -> List:
    """Imports objects from all python files in the given directories. Then
    uses verify to filter to the valid plugin objects.

    Takes the first plugin of a given name, if your plugin is not appearing
    check for naming conflicts."""
    plugins = []
    plugin_names = []

    existing_modules = list(sys.modules.keys())

    paths = [Path(path) for path in paths]
    for path in paths:
        if path.is_dir():

            sys.path.append(str(path))

            for module in path.iterdir():
                mod= _import_file(module, existing_modules, verify)
                if mod is not None and mod[1] not in plugin_names:
                    plugins.append(mod[0])
                    plugin_names.append(mod[1])

            sys.path.pop()

        elif path.is_file():
            sys.path.append(str(path.parent))
            mod = _import_file(path, existing_modules, verify)
            if mod is not None and mod[1] not in plugin_names:
                plugins.append(mod[0])
                plugin_names.append(mod[1])
            sys.path.pop()

    return plugins
