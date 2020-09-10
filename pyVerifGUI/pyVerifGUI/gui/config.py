"""Common configuration class

This class is to be distributed to every sub-class
"""

__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

import sys
import importlib
from os import PathLike
from oyaml import full_load, dump
from pathlib import Path
from qtpy import QtCore, QtWidgets, QtGui
import copy
from argparse import Namespace
from typing import Mapping, Union, Sequence

ConfigType = Mapping[str, Union[Sequence[str], str, int, float]]


class ConfigError(Exception):
    """Custom exception for configuration errors"""


# TODO clean up config, remove items that are not actually configuration or build related
# and move them elsewhere.
# The state that is currently being passed around via the config should be passed using
# signals instead. That is the correct way to operate. Also it would likely avoid some bugs.
# An example of this, is there should be an object that contains the actual config information,
# and that gets sent to every widget that needs it.


class Config(QtCore.QObject):
    """Class to manage common configuration data that every tab needs"""
    core_dir_path = None
    builds_path = None
    working_dir_path = None
    rtl_dir_path = None
    top_module = None
    build = None
    builds = []
    build_path = None
    status = {}
    config = {}
    model_exe = ""
    config_path = ""

    # signals when the build changes
    buildChanged = QtCore.Signal()
    # Passes the string location of the selected config
    new_config_selected = QtCore.Signal(str)

    log_output = QtCore.Signal(str)

    def __init__(self, arguments: Namespace, app_path: str):
        super().__init__()
        self.arguments = arguments
        # Not great, I'm kind of using config as this catch all object to pass around
        # for convenience. It's easy for me *to use*, but really not a nice implementation
        self.app_path = app_path

        self.new_config_dialog = ConfigDialog()

        self.new_build = False
        self.is_valid = False

    def __getitem__(self, item):
        """I don't like typing self.config.config everywhere so "directly" access the config dictionary"""
        return self.config[item]

    def validate_config(self, config: ConfigType) -> bool:
        """Checks as much of the config as possible to determine if it is valid"""
        # Import some important variables
        try:
            core_dir_path = Path(config["core_dir"])
        except KeyError:
            self.log_output.emit(
                "<CONFIG> missing 'verif_tools_path' or 'core_dir'")
            return False

        if not core_dir_path.exists() or not core_dir_path.is_dir():
            self.log_output.emit(
                f"<CONFIG> incorrect 'core_dir', verify the following path: {core_dir_path}"
            )

        # Test that all specified genfiles exist
        try:
            genfiles_dir = core_dir_path / config['genfiles_dir']
        except KeyError:
            self.log_output.emit(
                "<CONFIG> 'genfiles_dir' not found, skipping testbench generation config validation"
            )
            return True

        # Check if VerifTools path is correct
        try:
            verif_tools_path = config["verif_tools_path"]
            sys.path.insert(0, str(Path(core_dir_path) / verif_tools_path))
            import pySVTBgenerator
        except (ImportError, KeyError):
            self.log_output.emit(
                "<CONFIG> 'verif_tools_path' could not be validated")
            return False

        for genfile in [
                "monitor", "checker", "testcases", "assertions", "final_report"
        ]:
            try:
                if not (genfiles_dir / config[genfile]).exists():
                    self.log_output.emit(
                        f"<CONFIG> '{genfile}' could not be found, please verify path"
                    )
                    return False
            except KeyError:
                self.log_output.emit(
                    f"<CONFIG> '{genfile}' is not specified, please add it")
                return False

        # Test that include files exist
        for include in config["includes"]:
            if not (core_dir_path / include).exists():
                self.log_output.emit(
                    f"<CONFIG> file '{include}' does not exist, please check `includes`"
                )
                return False

        return True

    def _open_config(self, config: ConfigType):
        """Directly initialize configuration, manually assign members"""
        self.core_dir_path = Path(config["core_dir"])
        self.verif_tools_path = (self.core_dir_path /
                                 config["verif_tools_path"]).resolve()

        self.rtl_dir_paths = {}

        """Supports a few different variations:

        ---
        - dir1
        - dir2
        ---
        - dir1:
            recurse: bool
        - dir2
        ---
        dir1:
          recurse: bool
        dir2: {}

        Translates into final dictionary form
        """
        if type(config["rtl_dirs"]) is list:
            # list of paths or list of dicts
            for rtl_dir in config["rtl_dirs"]:
                if type(rtl_dir) is dict:
                    path = list(rtl_dir.keys())[0]
                    recurse = rtl_dir[path].get("recurse", True)
                else:
                    path = rtl_dir
                    recurse = True

                path = (self.core_dir_path / path).resolve()

                self.rtl_dir_paths.update({path: {"recurse": recurse}})
        else:
            for rtl_dir in config["rtl_dirs"]:
                opts = config["rtl_dirs"][rtl_dir]
                path = (self.core_dir_path / rtl_dir).resolve()

                self.rtl_dir_paths.update({path: {"recurse": opts.get("recurse", True)}})

        self.top_module = config["top_module"]
        self.config = config

        # Ensure builds directory exists
        self.builds_path = self.core_dir_path / Path(
            config["working_dir"]) / "builds"
        self.builds_path.mkdir(exist_ok=True, parents=True)

        # Generate list of builds
        self.builds = []
        for build_path in self.builds_path.iterdir():
            if build_path.is_dir():
                self.builds.append(build_path.name)

        if len(self.builds) == 0:
            self.open_build("master")

        self.buildChanged.emit()

    def open_config(self, location: PathLike):
        """Generate config from file"""
        if Path(location).exists():
            self.new_config_selected.emit(location)
            config = full_load(open(location))
            if self.validate_config(config):
                self.config_path = location
                self._open_config(config)
            else:
                QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Critical,
                    "Configuration is invalid!",
                    "Please correct your configuration.").exec_()
        else:
            # Open a new config dialog or something
            self.new_config_dialog.openDialog(location)

    def open_build(self, build: str):
        """Open an existing or a new build"""
        self.build = build
        self.build_path = self.builds_path / self.build
        self.build_status_path = self.build_path / "build_status.yaml"
        self.model_exe = str(
            (self.build_path /
             f"./obj_{self.top_module}/V{self.top_module}").resolve())
        # Build does not exist, open a new one
        if self.build not in self.builds:
            self.new_build = True
            self.build_path.mkdir(parents=True)
            self.status = {}
            self.dump_build()
        else:
            self.status = full_load(open(str(self.build_status_path)))

        self.working_dir_path = self.build_path
        self.buildChanged.emit()

    def dump_build(self):
        """Save build status to filesystem"""
        if self.build is not None:
            dump(self.status, open(str(self.build_status_path), "w"))


class ConfigDialog(QtWidgets.QDialog):
    """Dialog to create new configuration"""
    def __init__(self):
        super().__init__()
        self.setModal(True)

        self.layout = QtWidgets.QVBoxLayout(self)

        self.config_location = QtWidgets.QLineEdit(self)
        self.config_location.setReadOnly(True)
        self.config_text = QtWidgets.QTextEdit(self)

        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.addButton(self.button_box.Ok)
        self.button_box.addButton(self.button_box.Cancel)
        self.button_box.accepted.connect(self.saveConfig)
        self.button_box.rejected.connect(self.reject)

        self.layout.addWidget(self.config_location)
        self.layout.addWidget(self.config_text)
        self.layout.addWidget(self.button_box)

    def openDialog(self, file_loc: str):
        """Opens dialog to save file to specified location"""
        self.config_location.setText(file_loc)
        self.config_text.setText(self.configTemplate())
        self.setMinimumSize(700, 500)
        self.exec_()

    def saveConfig(self):
        """Saves filled-out configuration at file location"""
        filename = self.config_location.text()
        with open(filename, "w") as config:
            config.write(self.config_text.toPlainText())
        self.accept()

    def configTemplate(self) -> str:
        """Returns default config template"""
        return """
###############################################################################
# Minimum required for parsing

top_module:
repo_name:
# Base directory of core under test, should be relative to where you run gui.py
core_dir:
# working directory, relative to core_dir
working_dir:
# Directory containing rtl, relative to core_dir
rtl_dirs:
  - rtl:
      recurse: false
# Location of VerifTools repository, relative to core_dir
verif_tools_path:
"""
