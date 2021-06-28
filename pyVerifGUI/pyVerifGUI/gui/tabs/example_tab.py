###############################################################################
# @file pyVerifGUI/gui/tabs/example_tab.py
# @package pyVerifGUI.gui.tabs.example_tab
# @author David Lenfesty
# @copyright Copyright (c) 2021. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Example of a new GUI tab that can be written to extend functionality
##############################################################################
from typing import Tuple
from qtpy import QtWidgets

from pyVerifGUI.gui.base_tab import Tab, is_tab

#@is_tab
class MyTab(Tab):
    _placement = 9
    _name = "mytab"
    _display = "My Tab"

    def _post_init(self):
        self.layout = QtWidgets.QGridLayout(self)
        self.label = QtWidgets.QLabel("Hi I am a new tab", self)
        self.layout.addWidget(self.label)
        self.counter = 0

    def _verify(self) -> Tuple[bool, str]:
        return (False, "I want to show this not working")
        #return (True, "This is working")

    def update(self):
        self.counter += 1
        self.label.setText(f"I have been updated {self.counter} times")
