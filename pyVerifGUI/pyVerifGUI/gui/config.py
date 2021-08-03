###############################################################################
# @file pyVerifGUI/gui/config.py
# @package pyVerifGUI.gui.config
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Common configuration object. Distributed globally
##############################################################################
"""Common configuration class

This class is to be distributed to every sub-class
"""

import sys
import os
import importlib
from os import PathLike
from oyaml import safe_load, dump
from pathlib import Path
from qtpy import QtCore, QtWidgets, QtGui
import copy
from argparse import Namespace
from typing import Mapping, Union, Sequence, Optional, Any


from pyVerifGUI.gui.config_editor import ConfigEditorDialog

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
    # Signal to create new config at given location
    create_new_config = QtCore.Signal(str)

    log_output = QtCore.Signal(str)

    def __init__(self, arguments: Namespace, app_path: str):
        super().__init__()
        self.arguments = arguments
        # Not great, I'm kind of using config as this catch all object to pass around
        # for convenience. It's easy for me *to use*, but really not a nice implementation
        self.app_path = app_path

        self.thread_count = arguments.threads

        #self.new_config_dialog = ConfigDialog()

        self.new_build = False
        self.is_valid = False

    def reload_config(self):
        """Reloads configuration and build, e.g. after an edit"""
        build = self.build

        self.open_config(self.config_path)

        self.open_build(build, reload=True)

    def __getitem__(self, item):
        """I don't like typing self.config.config everywhere so "directly" access the config dictionary"""
        return self.config[item]

    def validate_config(self, config_location: os.PathLike) -> bool:
        """Checks as much of the config as possible to determine if it is valid"""
        dialog = ConfigEditorDialog(None)
        dialog.open_config(config_location)
        return not len(dialog._validate()) > 0

    def _open_config(self, config: ConfigType, location: str):
        """Directly initialize configuration, manually assign members"""
        self.core_dir_path = Path(location).parent / config["main"]["core_dir"]

        self.top_module = config["main"]["top_module"]
        self.config = config

        # Ensure builds directory exists
        self.builds_path = self.core_dir_path / Path(
            config["main"]["working_dir"]) / "builds"
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
            config = safe_load(open(location))
            if self.validate_config(location):
                self.config_path = location
                self._open_config(config, location)
            else:
                QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Critical,
                    "Configuration is invalid!",
                    "Please correct your configuration.").exec_()
        else:
            # Open a new config dialog or something
            self.config_path = location
            self.create_new_config.emit(location)

    def open_build(self, build: str, reload=False):
        """Open an existing or a new build"""
        self.build = build
        # TODO bug here... build can be passed in as None when saving config after not openning a build
        # This isn't exactly where the bug is, it just presents itself here.
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
            self.builds.append(build)
        else:
            self.status = safe_load(open(str(self.build_status_path)))

        self.working_dir_path = self.build_path
        if reload:
            self.buildChanged.emit()

    def dump_build(self):
        """Save build status to filesystem"""
        if self.build is not None:
            dump(self.status, open(str(self.build_status_path), "w"))


    def get_option(self, category: str, option: str) -> Optional[Any]:
        if category in self.config:
            if option in self.config[category]:
                return self.config[category][option]

        return None


    def set_option(self, category: str, option: str, value: Any):
        if not category in self.config:
            self.config[category] = {}

        self.config[category][option] = value
