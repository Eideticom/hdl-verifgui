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
from importlib import import_module, invalidate_caches
from typing import Callable, Any, List
from pathlib import Path
import inspect
import sys
import os

def import_plugins(directories: List[os.PathLike], verify: Callable[[Any], bool]) -> List:
    """Imports objects from all python files in the given directories. Then
    uses verify to filter to the valid plugin objects"""
    plugins = []

    directories = [Path(path) for path in directories]
    for dir in directories:
        if dir.is_dir():
            # Add to system search path
            sys.path.insert(0, str(dir))

            for module in dir.iterdir():
                if module.name == "__init__.py" or module.suffix != ".py":
                    continue

                invalidate_caches()
                mod = import_module(str(module.stem))
                for cls in inspect.getmembers(mod, inspect.isclass):
                    if verify(cls[1]):
                        plugins.append(cls[1])

            sys.path.pop(0)

    return plugins
