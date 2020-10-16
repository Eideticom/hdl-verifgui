###############################################################################
## File: gui/config.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Common configuration class

This class is to be distributed to every sub-class
"""

import sys
import os
import importlib
from os import PathLike
from yaml import full_load, dump
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
    # Signal to create new config at given location
    create_new_config = QtCore.Signal(str)

    log_output = QtCore.Signal(str)

    def __init__(self, arguments: Namespace, app_path: str):
        super().__init__()
        self.arguments = arguments
        # Not great, I'm kind of using config as this catch all object to pass around
        # for convenience. It's easy for me *to use*, but really not a nice implementation
        self.app_path = app_path

        #self.new_config_dialog = ConfigDialog()

        self.new_build = False
        self.is_valid = False

    def __getitem__(self, item):
        """I don't like typing self.config.config everywhere so "directly" access the config dictionary"""
        return self.config[item]

    def validate_config(self, config: ConfigType, config_location) -> bool:
        """Checks as much of the config as possible to determine if it is valid"""
        # Import some important variables
        try:
            core_dir_path = Path(config_location).parent / config["core_dir"]
        except KeyError:
            self.log_output.emit(
                "<CONFIG> missing 'core_dir'")
            return False

        if not core_dir_path.exists() or not core_dir_path.is_dir():
            self.log_output.emit(
                f"<CONFIG> incorrect 'core_dir', verify the following path: {core_dir_path}"
            )
            return False

        return True

    def _open_config(self, config: ConfigType, location: str):
        """Directly initialize configuration, manually assign members"""
        self.core_dir_path = Path(location).parent / config["core_dir"]

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
            if self.validate_config(config, location):
                self.config_path = location
                self._open_config(config, location)
            else:
                QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Critical,
                    "Configuration is invalid!",
                    "Please correct your configuration.").exec_()
        else:
            # Open a new config dialog or something
            self.create_new_config.emit(location)

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
            self.builds.append(build)
        else:
            self.status = full_load(open(str(self.build_status_path)))

        self.working_dir_path = self.build_path
        self.buildChanged.emit()

    def dump_build(self):
        """Save build status to filesystem"""
        if self.build is not None:
            dump(self.status, open(str(self.build_status_path), "w"))
