###############################################################################
# @file pyVerifGUI/gui/tabs/cocotb.py
# @package pyVerifGUI.gui.tabs.cocotb
# @author David Lenfesty
# @copyright Copyright (c) 2021. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief CocoTB test selector tab
##############################################################################
from typing import Tuple, List


from qtpy import QtWidgets, QtCore
from oyaml import full_load


from pyVerifGUI.gui.base_tab import Tab, is_tab
from pyVerifGUI.tasks.cocotb import *

"""
cocotb_tests.yaml (list of all collected tests - module->test dict)
cocotb_test_params.yaml (list of tests to run and their parameters - module->test dict)
cocotb_test_results.yaml (list of test results - straight list of tests w/ results and timing)

Won't have time to finish even layout probably:

Grid. First row has three columns. One is split vertically, select module and test.
Two is horizontal scrollable, full of vertical scrollables that have checkboxes for each param
Three is list of tests. For now, filter by ones selected by params, and colour based on state.
(we can do more advanced filtering later)

Probably needs buttons for loading/saving config (and run)

Also need a text box at the very bottom for overall test reporting.
"""


@is_tab
class CocoTBTab(Tab):
    _name = "cocotb"
    _display = "CocoTB"
    _placement = 3


    def _post_init(self):
        self.setLayout(QtWidgets.QGridLayout(self))

        self.module_selector = QtWidgets.QListView(self)
        self.test_selector = QtWidgets.QListView(self)

        self.params = QtWidgets.QScrollArea(self)
        self.params.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.tests_view = QtWidgets.QListView(self)
        self.buttons = QtWidgets.QWidget(self)

        self.report = QtWidgets.QTextBrowser(self)

        self.layout().addWidget(self.module_selector, 0, 0)
        self.layout().addWidget(self.test_selector, 1, 0)
        self.layout().addWidget(self.params, 0, 1, 2, 1)
        self.layout().addWidget(self.tests_view, 0, 2, 2, 1)
        self.layout().addWidget(self.buttons, 1, 2)
        self.layout().addWidget(self.report, 2, 0, 1, 3)


    def _verify(self) -> Tuple[bool, str]:
        return (True, "TODO, always for now though")


    def update(self):
        if self.config.build is None:
            return

        tests_path = self.config.working_dir_path / "cocotb_tests.yaml"
        if tests_path.exists():
            tests = full_load(open(str(tests_path), 'r'))

            modules = [mod for mod in tests]
            self.module_selector.setModel(ListModel(modules))
        else:
            # TODO clear everything out
            pass



    def _report(self) -> str:
        # TODO later, not important yet
        return ""


class ListModel(QtCore.QAbstractItemModel):
    """Basic model for just showing a list of things"""
    def __init__(self, items: List[str]):
        self.items = items


    def index(self, row: int, column: int, parent: QtCore.QModelIndex) -> QtCore.QModelIndex:
        return self.createIndex(row, column, self.items[row])


    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:
        return QtCore.QModelIndex()


    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        return len(self.items)


    def columnCount(self, parent: QtCore.QModelIndex) -> int:
        return 1


    def data(self, index: QtCore.QModelIndex, role: int) -> str:
        return self.items[index.row()]

