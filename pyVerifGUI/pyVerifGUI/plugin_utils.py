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
import inspect
import os

def import_plugins(directories: List[os.PathLike], verify: Callable[[Any], bool]) -> List:
    """Imports objects from all python files in the given directories. Then
    uses verify to filter to the valid plugin objects.

    Takes the first plugin of a given name, if your plugin is not appearing
    check for naming conflicts."""
    plugins = []
    plugin_names = []

    directories = [Path(path) for path in directories]
    for dir in directories:
        if dir.is_dir():
            for module in dir.iterdir():
                if module.name == "__init__.py" or module.suffix != ".py":
                    continue

                # I *would* use importlib, but that opens issues with
                # prior imports and can mess with importing things properly.
                mod = ModuleType(module.name)
                mod.__file__ = str(module.resolve())
                incoming_file = open(str(module)).read()
                exec(incoming_file, mod.__dict__)
                for cls in inspect.getmembers(mod, inspect.isclass):
                    if verify(cls[1]):
                        if cls[0] not in plugin_names:
                            plugins.append(cls[1])
                            plugin_names.append(cls[0])

    return plugins
