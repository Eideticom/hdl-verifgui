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
from PySide2.QtCore import QModelIndex


from qtpy import QtWidgets, QtCore
from oyaml import load, Loader


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
        self.report_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        self.select_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self.report_splitter)

        self.selector_widget = QtWidgets.QWidget(self.select_splitter)
        self.selector_widget.setLayout(QtWidgets.QVBoxLayout(self.selector_widget))
        self.module_selector = QtWidgets.QListView(self.selector_widget)
        self.test_selector = QtWidgets.QListView(self.selector_widget)
        self.selector_widget.layout().addWidget(self.module_selector)
        self.selector_widget.layout().addWidget(self.test_selector)

        self.param_container = QtWidgets.QWidget(self.select_splitter)
        self.param_container.setLayout(QtWidgets.QVBoxLayout(self.param_container))
        self.param_label = QtWidgets.QLabel("No widget selected!", self.param_container)
        self.params = QtWidgets.QScrollArea(self.param_container)
        self.params.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.param_container.layout().addWidget(self.param_label)
        self.param_container.layout().addWidget(self.params)

        self.tests_widget = QtWidgets.QWidget(self.select_splitter)
        self.tests_widget.setLayout(QtWidgets.QVBoxLayout(self.tests_widget))
        self.tests_view = QtWidgets.QListView(self.tests_widget)
        self.buttons = QtWidgets.QWidget(self.tests_widget)
        self.buttons.setLayout(QtWidgets.QHBoxLayout(self.buttons))
        self.save = QtWidgets.QPushButton("Save", self.buttons)
        self.save.clicked.connect(self.save_params)
        self.load = QtWidgets.QPushButton("Load", self.buttons)
        self.load.clicked.connect(self.load_params)
        self.buttons.layout().addWidget(self.load)
        self.buttons.layout().addWidget(self.save)
        self.tests_widget.layout().addWidget(self.tests_view)
        self.tests_widget.layout().addWidget(self.buttons)

        self.report = QtWidgets.QTextBrowser(self.report_splitter)

        self.layout().addWidget(self.report_splitter)
        self.report_splitter.addWidget(self.select_splitter)
        self.report_splitter.addWidget(self.report)

        self.select_splitter.addWidget(self.selector_widget)
        self.select_splitter.addWidget(self.param_container)
        self.select_splitter.addWidget(self.tests_widget)

        # This widget should be created/destroyed every time something is changed.
        # Cheap way to check if it needs to be destroyed.
        self.param_list_widget = None

        self.params_cache = {}


    def save_params(self):
        pass


    def load_params(self):
        pass


    def check_things(self):
        if self.param_list_widget is not None:
            for i in range(self.param_list_widget.layout().count()):
                print(self.param_list_widget.layout().itemAt(i).widget().selected())


    def _verify(self) -> Tuple[bool, str]:
        return (True, "TODO, always for now though")


    def update(self):
        if self.config.build is None:
            return

        tests_path = self.config.working_dir_path / "cocotb_tests.yaml"
        if tests_path.exists():
            # TODO why is Loader=Loader required?
            # Supposed to have been fixed in https://github.com/yaml/pyyaml/issues/266
            self._tests = load(open(str(tests_path), 'r'), Loader=Loader)

            modules = [mod for mod in self._tests]
            self.params_cache = {mod: {} for mod in self._tests}
            self.module_selector.setModel(ListModel(modules))
            self.module_selector.selectionModel().currentChanged.connect(self.on_module_selection)
            self.module_selector.setEnabled(True)
        else:
            self.module_selector.setEnabled(False)
            self.test_selector.setEnabled(False)


    def on_module_selection(self, current: QtCore.QModelIndex, _previous: QtCore.QModelIndex):
        """Handle when the user selects a different module"""
        module = current.data()
        self.active_module = module
        tests = [test for test in self._tests[module]]
        self.test_selector.setModel(ListModel(tests))
        self.test_selector.selectionModel().currentChanged.connect(self.on_test_selection)


    def on_test_selection(self, current: QtCore.QModelIndex, _previous: QtCore.QModelIndex):
        test = current.data()
        self.active_test = test
        test: CollectedTest = self._tests[self.active_module][test]
        if self.param_list_widget is not None:
            self.param_list_widget.deleteLater()

        self.param_list_widget = QtWidgets.QWidget(self.params)
        self.param_list_widget.setLayout(QtWidgets.QHBoxLayout(self.param_list_widget))

        for param in test.parameters:
            param_list = ParameterList(self.param_list_widget, param)
            self.param_list_widget.layout().addWidget(param_list)
            self.params.ensureWidgetVisible(self.param_list_widget)
            param_list.update_cache.connect(self.update_local_cache)

        self.params.setWidget(self.param_list_widget)
        self.params.show()
        self.param_label.setText(f"{self.active_module}::{self.active_test}")


    def update_local_cache(self):
        """After a click event on one of the test parameters, make sure that change is reflected in the cache"""
        cache_entry = []
        for i in range(self.param_list_widget.layout().count()):
            cache_entry.append(self.param_list_widget.layout().itemAt(i).widget().selected())

        self.params_cache[self.active_module][self.active_test] = cache_entry

        print(self.params_cache)


    def _report(self) -> str:
        # TODO later, not important yet
        return ""


class ParameterList(QtWidgets.QScrollArea):
    """Small widget to simplify displaying/checking parameters"""
    update_cache = QtCore.Signal()


    def __init__(self, parent, values: List[str]):
        super().__init__(parent)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_widget = QtWidgets.QWidget(self)
        self.scroll_widget.setLayout(QtWidgets.QVBoxLayout(self.scroll_widget))

        for val in values:
            check = QtWidgets.QCheckBox(val)
            self.scroll_widget.layout().addWidget(check)
            self.ensureWidgetVisible(self.scroll_widget)
            check.clicked.connect(self.on_click)

        self.setWidget(self.scroll_widget)
        self.show()
        self.scroll_widget.show()


    def selected(self) -> List[str]:
        out = []
        for i in range(self.scroll_widget.layout().count()):
            check = self.scroll_widget.layout().itemAt(i).widget()
            if check.isChecked():
                out.append(check.text())

        return out


    def on_click(self, _clicked: bool):
        self.update_cache.emit()


class ListModel(QtCore.QAbstractItemModel):
    """Basic model for just showing a list of things"""
    def __init__(self, items: List[str]):
        super().__init__()
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
        if role == QtCore.Qt.DisplayRole:
            return self.items[index.row()]

