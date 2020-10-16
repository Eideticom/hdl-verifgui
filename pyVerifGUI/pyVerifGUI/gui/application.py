###############################################################################
## File: gui/application.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Main application window definitions"""

from qtpy import QtCore, QtGui, QtWidgets
from psutil import cpu_percent, virtual_memory
from datetime import datetime
from pathlib import Path
import subprocess as sp
from argparse import Namespace
from typing import Callable

from pyVerifGUI.tasks import task_names

from .config import Config
from .menus import FileMenu, ViewMenu, HelpMenu
from .tabs.designview import DesignViewTab
from .tabs.lintview import LintViewTab
from .tabs.overview import OverviewTab


class Ui_MainWindow(QtWidgets.QMainWindow):
    """Main Qt window object
    
    This declares the overall structure of the application and is the top of the widget hierarchy.
    """

    # Signal to update GUI view
    update_view = QtCore.Signal()

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

        #### Tab creation and overview
        self.tabWidget = QtWidgets.QTabWidget(self.central_widget)
        self.tabWidget.setObjectName("tabWidget")
        self.overview_tab = OverviewTab(self.tabWidget, self.config)
        self.tabWidget.addTab(self.overview_tab, "Overview")
        self.design_tab = DesignViewTab(self.tabWidget, self.config)
        self.tabWidget.addTab(self.design_tab, "Hierarchy")
        self.lint_tab = LintViewTab(self.tabWidget, self.config)
        self.tabWidget.addTab(self.lint_tab, "Linter")
        # Start with first tab (overview) open
        self.tabWidget.setCurrentIndex(0)

        #### Progress bar widget
        self.progress_widget = ProgressBar(self.central_widget)
        # Signals
        self.overview_tab.runner.run_began.connect(
            self.progress_widget.beginTracking)
        self.overview_tab.runner.test_finished.connect(
            self.progress_widget.addOne)

        #### Main Layout
        self.layout.addWidget(self.tabWidget)
        self.layout.addWidget(self.progress_widget)

        #### Update signals
        # These are passed around when some event triggers an update of models, etc.
        self.config.buildChanged.connect(self.update_view)
        self.config.buildChanged.connect(self.checkDependancies)
        self.update_view.connect(self.updateTitle)
        self.update_view.connect(self.overview_tab.runner.updateBuildStatus)
        # Design tab will always update on a build change
        self.update_view.connect(self.design_tab.onUpdate)
        self.update_view.connect(self.lint_tab.modelUpdate)
        # update view once task completes
        self.overview_tab.runner.task_finished.connect(self.update_view)

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
        # Signals
        self.config.log_output.connect(self.logger.log_out)
        self.overview_tab.runner.run_results.connect(self.logger.write_output)
        self.overview_tab.runner.log_output.connect(self.logger.log_out)
        self.overview_tab.runner.run_stdout.connect(self.logger.stdout)
        self.design_tab.log_output.connect(self.logger.log_out)

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

        #### Re-run task dialog
        self.task_dialog = RerunTaskDialog(self)

        #### Add corner button widget to re-run tasks
        self.rerun_button = QtWidgets.QPushButton("Rerun Task", self)
        self.rerun_button.setEnabled(False)
        self.rerun_button.setStyleSheet("background-color: white")
        self.rerun_button.clicked.connect(self.task_dialog.run)
        self.tabWidget.setCornerWidget(self.rerun_button)
        # Update corner button on tab change
        self.tabWidget.currentChanged.connect(self.updateRerunButton)

        #### Summary report generation
        report_task = self.overview_tab.runner.getTask(task_names.report)
        report_task.addSummaryFn(self.lint_tab.generateSummary)

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
        if not self.closeTabEditor(self.lint_tab):
            event.ignore()
            return

        self.overview_tab.runner.killAllTasks()

        # Close if nothing is unsaved
        super().closeEvent(event)

    def updateRerunButton(self, index: int):
        """Called when tabs change to update the rerun button/dialog"""
        del index
        tab = self.tabWidget.currentWidget()

        if self.config.build is None:
            self.rerun_button.setEnabled(False)
            return

        # Change button depending on which tab is selected
        button_enabled = True
        if tab is self.design_tab:
            name = task_names.parse
        elif tab is self.lint_tab:
            name = task_names.lint
        else:
            name = ""
            fn = None
            button_enabled = False

        try:
            fn = self.overview_tab.runner.getTask(name).run
        except AttributeError:
            fn = None

        self.task_dialog.update(fn, name)
        self.rerun_button.setText(f"Re-run {name}")
        self.rerun_button.setEnabled(button_enabled)
        if button_enabled:
            self.rerun_button.setStyleSheet("background-color: green")
        else:
            self.rerun_button.setStyleSheet("background-color: white")

    def updateTitle(self):
        """Updates window title with build and configuration info"""
        self.setWindowTitle(
            f"Verification GUI - Build '{self.config.build}' from '{self.config.config_path}'"
        )

    def checkDependancies(self):
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
