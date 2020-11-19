###############################################################################
# @file pyVerifGUI/gui/application.py
# @package pyVerifGUI.gui.application
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
# All rights reserved
#
# @license Licensed under the BSD 3-Clause license.
# This license message must appear in all versions of this code including
# modified versions.
#
# @brief Main application window definitions
###############################################################################

from qtpy import QtCore, QtGui, QtWidgets
from psutil import cpu_percent, virtual_memory
from datetime import datetime
from pathlib import Path
import subprocess as sp
from argparse import Namespace
from typing import Callable

from pyVerifGUI.tasks import task_names
from pyVerifGUI.gui.tabs import implemented_tabs

from .config import Config
from .menus import FileMenu, ViewMenu, HelpMenu
from .tabs.overview import OverviewTab


class Ui_MainWindow(QtWidgets.QMainWindow):
    """Main Qt window object
    
    This declares the overall structure of the application and is the top of the widget hierarchy.
    """

    # Signal to update GUI view
    update_view = QtCore.Signal()

    globalUpdate = QtCore.Signal()

    def __init__(self, arguments: Namespace, app_path: str):
        super().__init__()

        # Housekeeping to identify the application
        self.setObjectName("MainWindow")
        self.setWindowTitle("Verification Tools")
        self.setWindowIcon(
            QtGui.QIcon(
                str(app_path / "assets/images/eideticom-logo-icon-only.png")))

        # Config is currently being used as a catch all for some global state
        self.config = Config(arguments, app_path)

        #### Central Layout
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QVBoxLayout(self.central_widget)

        # Set up tab widget with overview tab to start
        self.tabWidget = QtWidgets.QTabWidget(self.central_widget)
        self.tabWidget.setObjectName("tabWidget")
        self.overview_tab = OverviewTab(self, self.config)
        self.tabWidget.addTab(self.overview_tab, "Overview")
        #### Progress bar widget
        self.progress_widget = ProgressBar(self.central_widget)
        # Specific progress signals
        self.overview_tab.runner.run_began.connect(
            self.progress_widget.beginTracking)
        self.overview_tab.runner.test_finished.connect(
            self.progress_widget.addOne)

        #### Main Layout
        self.layout.addWidget(self.tabWidget)
        self.layout.addWidget(self.progress_widget)

        #### Update signals
        # This may couple everything together too much but it's easier for
        # everything to coalesce into a single spot for now and break it out
        # if it becomes an issue later.

        # Connect events into global update
        self.config.buildChanged.connect(self.onConfigUpdate) # Slot emits globalUpdate
        self.overview_tab.runner.task_finished.connect(self.globalUpdate)
        # Connect global update to various utilities
        self.globalUpdate.connect(self.updateTitle)
        self.globalUpdate.connect(self.checkDependencies)
        self.globalUpdate.connect(self.overview_tab.runner.updateBuildStatus)

        #### Message Output Box
        stdout_log_enabled = False
        stdout_out_enabled = False
        if arguments.verbose is not None:
            stdout_log_enabled = True
            if arguments.verbose > 1:
                stdout_out_enabled = True
        self.logger = Logger(self,
                             stdout_log_enabled=stdout_log_enabled,
                             stdout_out_enabled=stdout_out_enabled,
                             widget_enabled=True)
        # Connect log results
        self.config.log_output.connect(self.logger.log_out)
        self.overview_tab.runner.run_results.connect(self.logger.write_output)
        self.overview_tab.runner.log_output.connect(self.logger.log_out)
        self.overview_tab.runner.run_stdout.connect(self.logger.stdout)

        # TODO rearrange init sequence so it's more logically consistent
        # Add extra tabs
        self.addTabs()
        # Start with first tab (overview) open
        self.tabWidget.setCurrentIndex(0)

        #### Dock Widgets
        self.log_dock = QtWidgets.QDockWidget("Logging", self)
        self.log_tabs = QtWidgets.QTabWidget(self.log_dock)
        self.log_tabs.setTabPosition(self.log_tabs.South)
        self.log_tabs.addTab(self.logger.log_text, "Logging")
        self.log_tabs.addTab(self.logger.out_text, "Command Outputs")
        self.log_dock.setWidget(self.log_tabs)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.log_dock)

        #### Menubar etc.
        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setObjectName("menubar")
        self.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        #### Summary report generation
        report_task = self.overview_tab.runner.getTask(task_names.report)
        for tab in self.tabs:
            report_task.addTabSummary(tab)

        #### Menu bar
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.menu_bar.addMenu(FileMenu(self.menu_bar, self.config))
        self.menu_bar.addMenu(ViewMenu(self.menu_bar))
        self.menu_bar.addMenu(HelpMenu(self.menu_bar))
        self.setMenuBar(self.menu_bar)

        # If given, load config/build
        if arguments.config is not None:
            self.overview_tab.config_location.setText(arguments.config)
            self.overview_tab.loadConfig()
            if arguments.build is not None:
                combo_box = self.overview_tab.build_options
                builds = [
                    combo_box.itemText(i) for i in range(combo_box.count())
                ]
                if arguments.build not in builds:
                    combo_box.addItem(arguments.build)
                self.overview_tab.build_options.setCurrentText(arguments.build)
                self.overview_tab.selectBuild()

        if arguments.tests is not None:
            if arguments.build is not None:
                self.status_dock_widget.loadTests(from_file=arguments.tests)
            else:
                print(
                    "A build must be loaded before test selection can occur, remove --tests/-t or add a --build/-b"
                )
                exit(-1)

        #### CPU load / memory use indicator
        self.load_widget = QtWidgets.QLabel(self)
        self.statusBar().addPermanentWidget(self.load_widget)
        self.load_update_timer = QtCore.QTimer(self)
        self.load_update_timer.timeout.connect(self.updateLoad)
        self.load_update_timer.start(1000)  # update once per second
        self.updateLoad()

    def onConfigUpdate(self):
        """Handles updates coming from config.

        Runs some tasks before tabs get the update"""
        self.verifyTabs()
        self.globalUpdate.emit()

    def addTabs(self):
        """Adds all of the tabs"""
        # Instantiate every tab
        self.tabs = [tab(self.tabWidget, self.config) for tab in implemented_tabs]
        # Sort by provided placement index
        self.tabs.sort(key=lambda tab: tab._placement)

        for tab in self.tabs:
            self.tabWidget.addTab(tab, tab._display)

            tab.updateEvent.connect(self.globalUpdate)
            self.globalUpdate.connect(tab.update)
            tab.logOutput.connect(self.logger.log_out)

        # Verify and disable any tabs that don't validate
        self.verifyTabs()

    def verifyTabs(self):
        for inx in range(self.tabWidget.count()):
            tab = self.tabWidget.widget(inx)
            if getattr(tab, "_is_tab", False):
                rc, msg = tab._verify()
                # Disable tab and display tool text if validation fails
                self.tabWidget.setTabEnabled(inx, rc)
                self.tabWidget.setTabToolTip(inx, msg)


    def updateLoad(self):
        """Updates CPU load and memory usage status bar"""
        self.load_widget.setText(
            f"CPU: {cpu_percent()} - RAM: {virtual_memory()[2]}")

    def closeTabEditor(self, tab: QtWidgets.QWidget) -> bool:
        """Helper function to close the editors in a MessageView tab"""
        tab.showEditor()
        while len(tab.editor_tab.tabs) > 1:
            tab.editor_tab.tab_widget.setCurrentIndex(1)
            if not tab.editor_tab.closeTab(1):
                return False

        return True

    def closeEvent(self, event: QtGui.QCloseEvent):
        """Overridden here to save any open text editors"""
        for tab in self.tabs:
            if not tab.closeEditors():
                QtWidgets.QMessageBox.information(
                    "Unable to Close!",
                    f"The '{tab._display}' tab is blocking this application from closing."
                )
                return

        self.overview_tab.runner.killAllTasks()

        # Close if nothing is unsaved
        # TODO provide method to override, e.g. unsafely close
        super().closeEvent(event)

    def updateTitle(self):
        """Updates window title with build and configuration info"""
        self.setWindowTitle(
            f"Verification GUI - Build '{self.config.build}' from '{self.config.config_path}'"
        )

    # TODO this needs to only load on boot...
    # oooor be ran by the linter task
    def checkDependencies(self):
        """Check whether required programs have been installed"""
        try:
            sp.run(["verilator", "--help"], capture_output=True)
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Verilator Not Found!",
                                          "Verilator has not been found! Please ensure that it has been installed and is in your PATH.")


class ProgressBar(QtWidgets.QProgressBar):
    """Custom progress bar"""
    def __init__(self, parent):
        super().__init__(parent)
        self.hide()

    def beginTracking(self, task_name: str, task_num: int):
        """Shows the progress bar and updates text"""
        self.setMaximum(task_num)
        self.setValue(0)
        self.setFormat(f"{task_name}: %v / %m")
        self.show()

    def addOne(self):
        """Adds one digit to the progress"""
        value = self.value() + 1
        self.setValue(value)

        if value == self.maximum():
            self.hide()


class RerunTaskDialog(QtWidgets.QDialog):
    """Dialog to confirm re-running of a task"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Re-run Task")
        self.setModal(True)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.msg_text = QtWidgets.QLabel("No build selected!", self)
        self.buttons = QtWidgets.QDialogButtonBox(self)
        self.buttons.addButton(self.buttons.Ok)
        self.buttons.addButton(self.buttons.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.msg_text)
        self.layout.addWidget(self.buttons)

        self.fn = None

    def update(self, fn: Callable, name: str):
        """Updates info.

        fn - Function to call on user accept
        name - Name to fill in on window title
        """
        self.fn = fn
        self.setWindowTitle(f"Re-run {name}")
        self.msg_text.setText(f"Are you sure you want to re-run {name}?")

    def run(self):
        """Opens dialog and asks for confirmation of running"""

        if self.fn is None:
            self.setWindowTitle(f"Re-run Task")
            self.msg_text.setText("No task to run!")
            self.exec_()
        else:
            if self.exec_():
                # User confirmed, we want to run the correct function
                self.fn()


class Logger(QtCore.QObject):
    """Base logger to write outputs to different places"""
    def __init__(self,
                 parent,
                 stdout_log_enabled=False,
                 stdout_out_enabled=False,
                 widget_enabled=False):
        super().__init__(parent)

        self.log_text = QtWidgets.QPlainTextEdit(parent)
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(500)

        self.out_text = QtWidgets.QPlainTextEdit(parent)
        self.out_text.setReadOnly(True)
        self.out_text.setMaximumBlockCount(2000)

        self.stdout_log_enabled = stdout_log_enabled
        self.stdout_out_enabled = stdout_out_enabled
        self.widget_enabled = widget_enabled

    def log_out(self, text: str):
        """Write general log text"""
        for line in text.splitlines():
            now = datetime.now().strftime("%H:%M:%S")
            if self.widget_enabled:
                self.log_text.appendPlainText(f"[{now}]: {line}")
            if self.stdout_log_enabled:
                print(f"[LOG - {now}]:    {line}")

    def stdout(self, name: str, line: str):
        """Slot for continuous output"""
        text = f"[{name}] stdout:    {line.rstrip()}"
        if self.widget_enabled:
            self.out_text.appendPlainText(text)
        if self.stdout_out_enabled:
            print(text)

    def write_output(self,
                     name: str,
                     rc: int,
                     stdout: str,
                     stderr: str,
                     time: float = None):
        """Write output to text box

        time is required as an optional argument to allow for directly connecting to results slots
        """
        # We ignore stdout because it should have been caught by stdout()
        del rc, stdout, time
        for line in stderr.splitlines():
            text = f"[{name}] stderr:    {line}"
            if self.widget_enabled:
                self.out_text.appendPlainText(text)
            if self.stdout_out_enabled:
                print(text)
