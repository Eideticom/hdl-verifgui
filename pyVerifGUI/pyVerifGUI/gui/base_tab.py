###############################################################################
# @file pyVerifGUI/gui/base_tab.py
# @package pyVerifGUI.gui.base_tab
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
# All rights reserved
#
# @license Licensed under the BSD 3-Clause license.
# This license message must appear in all versions of this code including
# modified versions.
#
# @brief Base class for any new tab.
###############################################################################

from qtpy import QtWidgets, QtCore

from typing import Optional, Tuple
from pathlib import Path
import sys
import os

from pyVerifGUI.gui.config import Config

def is_tab(cls):
    """Decorator to explicitly classify an object as a tab.

    Using this vs just checking if the tab inherits from Tab allows
    you to build base tabs for common functionality.
    """
    cls._is_tab = True
    return cls

class Tab(QtWidgets.QWidget):
    # Change this to affect the placement of a tab
    # Lower numbers get placed first, ties are resolved however sorted() does it
    _placement = -1

    """Base class to define a tab"""
    def __init__(self, parent, config: Config):
        """Failure here should simply mean the tab is unavailable.
        
        If possible, some descriptive string describing the reason should be provided,
        and that string will be displayed as the mousover text for the disabled tab."""
        super().__init__(parent)

        self.config = config

        # Needs more error and other handling as well
        try:
            self._post_init()
        except NotImplementedError:
            print(f"Plugin {self._name} did not have _post_init defined")
            sys.exit()

    def _convert_path(self, path_to_convert: os.PathLike) -> Path:
        """Converts a string or path or something to an absolute path relative
        to config."""

    def log(self, str) -> str:
        """Writes to logging signal with the tab's information"""
        self.logOutput.emit(f"{str}\n")

    def closeEditors(self) -> bool:
        """Re-implement in child class to provide a gateway to safely closing
        any editors or anything similar which requires saving functionality.

        Return False if you can't close without extra intervention.
        """
        return True

    #### ------
    # Functions the plugin or whatever needs to define for common functionality
    def _post_init(self) -> Optional[str]:
        """To be implemented by the new tab, must operate completely based on config

        Returns:
            Either None or a string describing why init could not happen.
        """
        raise NotImplementedError

    def _verify(self) -> Tuple[bool, str]:
        """Verifies that all components are correct. If not, gives a reason string"""
        raise NotImplementedError

    @property
    def _name(self) -> str:
        """backend name of module to use for configs and the such"""
        raise NotImplementedError

    @property
    def _display(self) -> str:
        """Text to display on tab, buttons, etc."""
        raise NotImplementedError

    #### ------
    # Signals and slots
    # General update-causing events
    updateEvent = QtCore.Signal()
    # Logging events
    logOutput = QtCore.Signal(str)

    def update(self):
        """Update displayed information

        It's up to the implementation to ignore these events when there is no need
        to update.

        XXX There is a risk of an infinite loop if updates and update
        events are not handled properly, and the update function emits
        updateEvent.
        """
        raise NotImplementedError

    #### ------
    # Optional implementations
    def _report(self) -> str:
        """Text report, will get accumulated into a larger report.

        Ideally return markdown formatted text
        """
        return ""
