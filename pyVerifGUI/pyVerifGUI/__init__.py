#!/usr/bin/env python3

###############################################################################
## File: __main__.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""GUI tool to manage verification"""

__version__ = "0.1.0"

import sys

if sys.version_info < (3, 7):
    print("Python >= 3.7 required!")
    exit(-1)

from qtpy import QtWidgets
from qtpy.QtWidgets import QApplication, QMainWindow
from pyVerifGUI.gui.application import Ui_MainWindow
from pathlib import Path
import argparse

import pyVerifGUI.pytest_integration

def main():
    arguments = argparse.ArgumentParser(description="GUI to run Eideticom verification tools.")
    arguments.add_argument("--verbose", "-v", action="count",
                           help="Enable verbose command line output")
    arguments.add_argument("--config", "-c", type=str, help="Pre-select a configuration to load")
    arguments.add_argument("--build", "-b", type=str, help="Pre-select a build to open")
    arguments.add_argument("--user", "-u", type=str, help="Define a username for waivers")
    arguments.add_argument("--tests", "-t", type=str, help="Load a file with test selections. Will not work without a build selected.")
    arguments.add_argument("--tabs", type=str, action="append", default=[],
                           help="Add another directory to look for tabs in.")
    arguments.add_argument("--tasks", type=str, action="append", default=[],
                           help="Add another directory to look for tasks in.")
    arguments.add_argument("--threads", "-j", type=int, default=0,
                           help="Select default number of threads to give to tasks")
    arguments = arguments.parse_args()

    app = QApplication(sys.argv)
    ui = Ui_MainWindow(arguments, Path(__file__).parent)

    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()