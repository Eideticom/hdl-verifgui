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
from typing import Tuple, List, Union, Any, Dict
import itertools


from qtpy import QtWidgets, QtCore, QtGui
from oyaml import load, Loader, dump


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
        self.param_label = QtWidgets.QLabel("No test selected!", self.param_container)
        self.params = QtWidgets.QScrollArea(self.param_container)
        self.params.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.param_container.layout().addWidget(self.param_label)
        self.param_container.layout().addWidget(self.params)

        self.tests_widget = QtWidgets.QWidget(self.select_splitter)
        self.tests_widget.setLayout(QtWidgets.QVBoxLayout(self.tests_widget))
        self.tests_view = QtWidgets.QTableView(self.tests_widget)
        self.buttons = QtWidgets.QWidget(self.tests_widget)
        self.buttons.setLayout(QtWidgets.QHBoxLayout(self.buttons))
        self.save = QtWidgets.QPushButton("Save", self.buttons)
        self.save.clicked.connect(self.save_params)
        self.load = QtWidgets.QPushButton("Load", self.buttons)
        self.load.clicked.connect(self.load_params)
        # Can't use this, need to save list of tests before I start the test :(
        #overview_tab = self.parent().parent().parent().overview_tab
        #self.run_button = overview_tab.runner.createTaskButton("cocotb_run", self.buttons)
        self.run_button = QtWidgets.QPushButton("Run")
        self.run_button.clicked.connect(self.run_tests)
        self.buttons.layout().addWidget(self.load)
        self.buttons.layout().addWidget(self.save)
        self.buttons.layout().addWidget(self.run_button)
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


    def run_tests(self):
        # TODO a few more smarts here, ideally would just be another instance of the buttons
        # in the overview.
        with open(str(self.config.working_dir_path / "cocotb_test_list"), "w") as f:
            for test in self.tests_view.model().tests:
                f.write(f"{test}\n")

        runner = self.parent().parent().parent().parent().overview_tab.runner
        runner.startTaskByName("cocotb_run")


    def save_params(self):
        # TODO likely there are some edge cases still based on off-expected behaviour, but this should be good for now
        with open(str(self.config.working_dir_path / "cocotb_test_params.yaml"), "w") as f:
            dump(self.params_cache, f)


    def load_params(self):
        # TODO load params by default
        with open(str(self.config.working_dir_path / "cocotb_test_params.yaml")) as f:
            self.params_cache = load(f, Loader=Loader)

        # Update current test selection to reflect newly loaded parameters
        if self.test_selector.selectionModel() is not None:
            idx = self.test_selector.selectionModel().currentIndex()
            if idx.isValid():
                self.on_test_selection(idx, None)

        # Used to ensure that list of tests is updated
        self.update_local_cache()


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
        tests = [test for test in self._tests[module]]
        self.test_selector.setModel(ListModel(tests))
        self.test_selector.selectionModel().currentChanged.connect(self.on_test_selection)


    def on_test_selection(self, current: QtCore.QModelIndex, _previous: QtCore.QModelIndex):
        test = current.data()
        self.active_test = test
        self.active_module = self.module_selector.selectionModel().currentIndex().data()
        test: CollectedTest = self._tests[self.active_module][test]
        if self.param_list_widget is not None:
            self.param_list_widget.deleteLater()

        self.param_list_widget = QtWidgets.QWidget(self.params)
        self.param_list_widget.setLayout(QtWidgets.QHBoxLayout(self.param_list_widget))

        # Grab cached parameters for this test
        cached_selections = self.params_cache[self.active_module].get(self.active_test, [[] for _ in test.parameters])

        for i in range(len(test.parameters)):
            param = test.parameters[i]

            # Build widget and add to list
            param_list = ParameterList(self.param_list_widget, param, cached_selections[i])
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

        # Update list of tests to run
        tests = []
        for mod in self.params_cache:
            for test in self.params_cache[mod]:
                for param_list in itertools.product(*self.params_cache[mod][test]):
                    tests.append(f"{mod}::{test}[{'-'.join(param_list)}]")

        old_model = self.tests_view.model()
        if old_model is not None:
            old_model.deleteLater()
        # TODO test status
        self.tests_view.setModel(TestModel(tests, {}))


    def _report(self) -> str:
        # TODO later, not important yet
        return ""


class ParameterList(QtWidgets.QScrollArea):
    """Small widget to simplify displaying/checking parameters"""
    update_cache = QtCore.Signal()


    def __init__(self, parent, values: List[str], checked_values: List[str]):
        super().__init__(parent)

        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_widget = QtWidgets.QWidget(self)
        self.scroll_widget.setLayout(QtWidgets.QVBoxLayout(self.scroll_widget))

        for val in values:
            check = QtWidgets.QCheckBox(val)
            self.scroll_widget.layout().addWidget(check)
            self.ensureWidgetVisible(self.scroll_widget)
            check.clicked.connect(self.on_click)
            if val in checked_values:
                check.setChecked(True)

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


class TestModel(QtCore.QAbstractItemModel):
    """Model for displaying selected tests and their run status."""
    headers = ["Test Name", "Status", "Time"]


    def __init__(self, tests: List[str], test_status: Dict[str, Dict[str, Union[str, float]]]):
        super().__init__()
        self.tests = tests
        self.test_status = test_status


    def index(self, row: int, column: int, parent: QtCore.QModelIndex) -> QtCore.QModelIndex:
        return self.createIndex(row, column, self.tests[row])


    def parent(self, child: QtCore.QModelIndex) -> QtCore.QModelIndex:
        return QtCore.QModelIndex()


    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        return len(self.tests)


    def columnCount(self, parent: QtCore.QModelIndex) -> int:
        # TODO some way to keep TestStatus and self.headers synced?
        return len(self.headers)


    def data(self, index: QtCore.QModelIndex, role: int) -> Any:
        # NOTE: can't use these methods on the index, because apparently they call the model's methods
        # Not sure how I didn't find this until now
        # test = index.data()
        test: str = self.tests[index.row()]
        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return test
            elif index.column() == 1:
                if test in self.test_status:
                    return self.test_status[test]["status"]
                else:
                    return "Unstarted"
            elif index.column() == 2:
                if test in self.test_status:
                    if self.test_status[test].get("time", None) is not None:
                        return f"{self.test_status[test]['time']}s"

                return "N/A"

        elif role == QtCore.Qt.BackgroundColorRole:
            if test not in self.test_status:
                return QtGui.QColor(0xD0, 0xD0, 0xD0) # Default colour

            status = self.test_status[test]["status"]
            if status == "passed":
                return QtGui.QColor(0x00, 0xD0, 0x00) # Green
            elif status == "failed":
                return QtGui.QColor(0xD0, 0x00, 0x00) # Red
            elif status == "running":
                return QtGui.QColor(0xD4, 0xD4, 0x00) # Yellow ?


    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int) -> Any:
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.headers[section]

