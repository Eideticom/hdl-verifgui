###############################################################################
# @file pyVerifGUI/gui/tabs/overview.py
# @package pyVerifGUI.gui.tabs.overview
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Definition of the Overview tab. Frontend for running tasks
##############################################################################

from qtpy import QtCore, QtWidgets
from yaml import dump
import subprocess as sp
import pyparsing as pp
from pathlib import Path
import shutil
import os

from pyVerifGUI.gui.tabs.runnerwidget import RunnerGUI as NewRunnerGUI
from pyVerifGUI.gui.editor import Editor
from pyVerifGUI.gui.config_editor import ConfigEditorDialog


class OverviewTab(QtWidgets.QWidget):
    """Provides an overview of the current status.

    Allows you to run jobs for builds and view what is finished.
    """
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        self.main_layout = QtWidgets.QGridLayout(self)
        self.main_layout.setObjectName("main_layout")
        self.config_widget = QtWidgets.QWidget(self)
        #self.runner = RunnerGUI(self, config)
        self.runner = NewRunnerGUI(self, config)
        self.main_layout.addWidget(self.config_widget)
        self.setLayout(self.main_layout)
        self.config_layout = QtWidgets.QGridLayout(self.config_widget)
        self.config_layout.setObjectName("config_layout")

        #### launch config editor
        self.config_dialog = ConfigEditorDialog(self)
        self.open_config_editor = QtWidgets.QPushButton("Create/Edit Configuration", self)
        self.open_config_editor.clicked.connect(self._open_config_editor)
        self.config.create_new_config.connect(self.config_dialog.open)
        self.config_selected = False

        # File select for config
        self.config_label = QtWidgets.QLabel(self.config_widget)
        self.config_label.setText("Configuration")
        self.config_location = QtWidgets.QLineEdit(self.config_widget)
        self.config_location.setObjectName("config_location")
        self.config_browse = QtWidgets.QPushButton(self.config_widget)
        self.config_browse.setObjectName("config_browse")
        self.config_browse.setText("Browse")
        self.config_load = QtWidgets.QPushButton(self.config_widget)
        self.config_load.setObjectName("config_load")
        self.config_load.setText("Load")
        self.config_layout.addWidget(self.config_label, 0, 0)
        self.config_layout.addWidget(self.config_location, 0, 1)
        self.config_layout.addWidget(self.config_browse, 0, 2)
        self.config_layout.addWidget(self.config_load, 0, 3)
        self.config_layout.addWidget(self.open_config_editor, 0, 4)

        # Signals for config selection
        self.config_browse.clicked.connect(self.openBrowseDialog)
        self.config_load.clicked.connect(self.loadConfig)

        # Build selection
        self.build_label = QtWidgets.QLabel(self.config_widget)
        self.build_label.setText("Build")
        self.build_options = QtWidgets.QComboBox(self.config_widget)
        self.build_options.setObjectName("build_options")
        self.build_select = QtWidgets.QPushButton(self.config_widget)
        self.build_select.setObjectName("build_select")
        self.build_select.setText("Select Build")
        self.build_select.setEnabled(False)
        self.config_layout.addWidget(self.build_label, 1, 0)
        self.config_layout.addWidget(self.build_options, 1, 1)
        self.config_layout.addWidget(self.build_select, 1, 2)

        self.build_select.clicked.connect(self.selectBuild)

        #### Splitter for git info vs. config editor
        self.info_config_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Vertical, self)

        #### Git status
        self.git_widget = QtWidgets.QWidget(self.info_config_splitter)
        self.git_layout = QtWidgets.QVBoxLayout(self.git_widget)
        self.git_label = QtWidgets.QLabel("Git Status", self.git_widget)
        self.git_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.git_status = QtWidgets.QTextEdit(self.git_widget)
        self.git_status.setReadOnly(True)
        self.git_layout.addWidget(self.git_label)
        self.git_layout.addWidget(self.git_status)
        self.info_config_splitter.addWidget(self.git_widget)
        self.info_config_splitter.setSizes([100, 100])

        self.main_layout.addWidget(self.info_config_splitter)

        # Build/config status signals
        self.config.new_config_selected.connect(self.config_has_been_selected)
        self.config.buildChanged.connect(self.gitStatus)

        self.main_layout.addWidget(self.runner, 6, 0, 1, 2)

    def _open_config_editor(self, clicked=False, path=None) -> bool:
        """Slot that opens new configuration editor dialog"""
        config_dialog = ConfigEditorDialog(self)
        if not path:
            if not self.config_selected:
                rc = config_dialog.open()
                config_dialog.deleteLater()
                return rc
            path = self.config_location.text()

        rc = config_dialog.open(path)
        config_dialog.deleteLater()
        return rc

    def config_has_been_selected(self, _path: str):
        """Updates config to clarify editing"""
        self.config_selected = True

    def loadConfigInEditor(self, location: str):
        """Slot that loads the emitted config location into the editor"""
        self.config_editor.loadFile(location, always_new=False)

    def gitStatus(self):
        """Runs `git status` and updates text box"""
        if self.config.core_dir_path is not None:
            out = sp.run(["git", "status"],
                         capture_output=True,
                         cwd=self.config.core_dir_path)
            self.git_status.setPlainText(str(out.stdout, 'utf-8'))
        else:
            self.git_status.setPlainText("No config selected!")

    def openBrowseDialog(self, checked=False):
        """Opens a file browser dialog to search for a configuration file."""
        del checked
        (filename, ok) = QtWidgets.QFileDialog.getOpenFileName(
            self.config_browse, "Select Configuration", "./",
            "Configuration Files (*.yaml)")
        if not filename.endswith(".yaml"):
            filename += ".yaml"

        if ok:
            self.config_location.setText(filename)
            self.loadConfig()

    def loadConfig(self, checked=False):
        """Loads the configuration file selected by the config_location text box"""
        del checked
        if self.config_location.text() != "":
            self.config.open_config(self.config_location.text())
            builds = self.config.builds.copy()
            builds.insert(0, "New")
            self.build_options.clear()
            self.build_options.addItems(builds)
            self.build_select.setEnabled(True)
            self.gitStatus()

    def selectBuild(self, checked=False):
        """Selects and displays the build chosen in the drop down menu"""
        del checked
        ok = False
        if self.build_options.currentText() == "New":
            build, ok = QtWidgets.QInputDialog.getText(
                self.build_options, "Create New Build",
                "Please enter a name for the new build",
                QtWidgets.QLineEdit.Normal, "")

            if not ok:
                return
        else:
            build = self.build_options.currentText()

        self.config.open_build(build)
        self.loadConfig()  # Re-populate build_options
        self.config.num_threads = self.runner.thread_select.value()
        self.build_options.setCurrentText(build)
