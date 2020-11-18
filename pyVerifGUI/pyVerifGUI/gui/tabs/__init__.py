###############################################################################
# @file pyVerifGUI/gui/tabs/__init__.py
# @package pyVerifGUI.gui.tabs
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Accumulates tabs in a single import place
##############################################################################

from pathlib import Path
from importlib import import_module
import inspect

implemented_tabs = []

# Iter over every class in every module
# if it has _is_tab == True, then add to the list
# import all functions from all files that are not 'decorator.py'
for module in Path(__file__).parent.iterdir():
    if module.name == '__init__.py' or not module.suffix == ".py":
        continue

    mod = import_module("." + str(module.stem), __name__)
    for cls in inspect.getmembers(mod, inspect.isclass):
        if getattr(cls[1], "_is_tab", False):
            implemented_tabs.append(cls[1])
