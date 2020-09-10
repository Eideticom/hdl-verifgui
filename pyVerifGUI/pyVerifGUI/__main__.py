#!/usr/bin/env python3
"""
GUI tool to manage verification
"""

__author__ = 'David Lenfesty'
__copyright__ = 'Copyright (c) 2020. Eideticom Inc. All rights reserved.'
__license__ = "NA"
__version__ = "0.1.0"

import sys

if sys.version_info < (3, 7):
    print("Python >= 3.7 required!")
    exit(-1)

from qtpy import QtWidgets
from qtpy.QtWidgets import QApplication, QMainWindow
from pyVerifGUI.gui import Ui_MainWindow
from pathlib import Path
import argparse

def main():
    arguments = argparse.ArgumentParser(description="GUI to run Eideticom verification tools.")
    arguments.add_argument("--verbose", "-v", action="count",
                           help="Enable verbose command line output")
    arguments.add_argument("--config", "-c", type=str, help="Pre-select a configuration to load")
    arguments.add_argument("--build", "-b", type=str, help="Pre-select a build to open")
    arguments.add_argument("--user", "-u", type=str, help="Define a username for waivers")
    arguments.add_argument("--tests", "-t", type=str, help="Load a file with test selections. Will not work without a build selected.")
    arguments = arguments.parse_args()

    app = QApplication(sys.argv)
    ui = Ui_MainWindow(arguments, Path(__file__).parent)

    ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
