###############################################################################
# @file pyVerifGUI/gui/config_editor.py
# @package pyVerifGUI.gui.config_editor
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Configuration editor dialog
##############################################################################
from qtpy import QtWidgets, QtCore, QtGui
from pathlib import Path
from functools import partialmethod
from yaml import safe_load, dump
from typing import List
from glob import glob
import os


from typing import Callable, Any, Optional
from functools import partial


# TODO rework this widget so exception passing out of a constructor is not required.
class ConfigNotSelected(Exception):
    """Exception for passing errors up out of editor object"""

class ConfigEditorDialog(QtWidgets.QDialog):
    """Dialog for editing config"""
    def __init__(self, parent):
        super().__init__(parent)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.editor = None

    def open(self, config_path = None) -> bool:
        """Opens dialog for editing config

        Returns one when dialog succeeds
        """
        # XXX Would be better to add in proper signalling to change path
        # rather than just rebuilding.
        if self.layout.count():
            self.layout.removeWidget(self.editor)
            self.editor.deleteLater()

        try:
            self.editor = ConfigEditor(self, config_path)
        except ConfigNotSelected:
            return False

        self.editor.save.clicked.connect(self.accept)
        self.layout.addWidget(self.editor)

        return self.exec_()


class ConfigEditor(QtWidgets.QWidget):
    """Widget to create or edit configuration files in a consistent manner"""
    def __init__(self, parent=None, config_path=None):
        super().__init__(parent)

        self._core_dir_path = None

        self.layout = QtWidgets.QGridLayout(self)

        # core dir
        self.core_label = QtWidgets.QLabel("Top level location", self)
        self.core_path = QtWidgets.QLineEdit(self)
        self.core_path.setReadOnly(True)
        self.browse_core_path = QtWidgets.QPushButton("Browse", self)
        self.browse_core_path.clicked.connect(self.browse_for_core_dir)
        # working_dir
        self.working_label = QtWidgets.QLabel("Working directory (to store builds in)", self)
        self.working_path = QtWidgets.QLineEdit(self)
        self.browse_working_path = QtWidgets.QPushButton("Browse", self)
        self.browse_working_path.clicked.connect(self.browse_for_working_dir)
        # top_module
        self.top_label = QtWidgets.QLabel("Top-level module", self)
        self.top_module = QtWidgets.QLineEdit(self)
        # Repo name
        self.repo_label = QtWidgets.QLabel("Repository name (optional)", self)
        self.repo_name = QtWidgets.QLineEdit(self)
        # cocotb/pytest folder (temp until config gets re-written)
        self.cocotb_label = QtWidgets.QLabel("CocoTB/pytest location", self)
        self.cocotb_path = QtWidgets.QLineEdit(self)
        self.cocotb_browse = QtWidgets.QPushButton("Browse", self)
        self.cocotb_browse.clicked.connect(self.browse_for_cocotb_dir)

        # rtl
        self.rtl = RtlIncludes(self, config_path)

        # Extra parser arguments
        # XXX parser should just be integrated, so these should be options
        self.parser_label = QtWidgets.QLabel("Extra parser arguments (optional)", self)
        self.parser_args = QtWidgets.QPlainTextEdit(self)

        # Extra verilator lint arguments
        self.verilator_label = QtWidgets.QLabel("Verilator linting arguments (optional)", self)
        self.verilator_args = QtWidgets.QPlainTextEdit(self)

        # Buttons!
        self.validate_button = QtWidgets.QPushButton("Validate", self)
        self.validate_button.clicked.connect(self.validate_w_dialog)
        self.save = QtWidgets.QPushButton("Save", self)
        self.save.clicked.connect(self.save_cfg)

        self.coverage_reasons = OptionList(self, self.get_option, self.set_option)
        self.coverage_label = QtWidgets.QLabel("Extra Coverage Reasons", self)

        #### Layout
        self.layout.setColumnStretch(0, 1)
        self.layout.addWidget(self.core_label, 0, 0)
        self.layout.addWidget(self.core_path, 1, 0)
        self.layout.addWidget(self.browse_core_path, 1, 1)
        self.layout.addWidget(self.working_label, 2, 0)
        self.layout.addWidget(self.working_path, 3, 0)
        self.layout.addWidget(self.browse_working_path, 3, 1)
        self.layout.addWidget(self.cocotb_label, 4, 0)
        self.layout.addWidget(self.cocotb_path, 5, 0)
        self.layout.addWidget(self.cocotb_browse, 5, 1)
        self.layout.addWidget(self.top_label, 6, 0)
        self.layout.addWidget(self.top_module, 7, 0)
        self.layout.addWidget(self.repo_label, 8, 0)
        self.layout.addWidget(self.repo_name, 9, 0)
        self.layout.addWidget(self.rtl, 10, 0)
        self.layout.addWidget(self.parser_label, 11, 0)
        self.layout.addWidget(self.parser_args, 12, 0)
        self.layout.addWidget(self.verilator_label, 13, 0)
        self.layout.addWidget(self.verilator_args, 14, 0)
        self.layout.addWidget(self.coverage_label, 15, 0)
        self.layout.addWidget(self.coverage_reasons, 16, 0)
        self.layout.addWidget(self.validate_button, 17, 0, 1, 2)
        self.layout.addWidget(self.save, 18, 0, 1, 2)

        if config_path is None:
            dialog = QtWidgets.QFileDialog.getSaveFileName
            config_path, _type = dialog(self,
                                        "Create a configuration file:",
                                        "./",
                                        "YAML Files (*.yaml)")

            if not config_path:
                raise ConfigNotSelected()

        # Update config path for RTL
        # XXX shouldn't be this direct, unsure how to re-work so constructor is called later on
        # TODO causes issue when path is not selected
        self.rtl.config_path = Path(config_path)
        self.load_config(config_path)


    def get_option(self, category: str, option: str) -> Optional[Any]:
        if category in self.config:
            if option in self.config[category]:
                return self.config[category][option]

        return None


    def set_option(self, category: str, option: str, value: Any):
        if category not in self.config:
            self.config[category] = {}

        self.config[category][option] = value


    def browse_for_core_dir(self):
        """Browse for a directory"""
        if self.core_path.text():
            start_path = self.core_path.text()
        else:
            start_path = str(self._core_dir_path)

        dialog = QtWidgets.QFileDialog.getExistingDirectory
        path = dialog(self, "Select Base Directory", start_path)

        # Need to handle it relative to configuration or something
        if path:
            path = os.path.relpath(path, self.config_path.parent)
            self.core_path.setText(path)
            self._core_dir_path = Path(path)
            self.rtl.set_core_dir(self._core_dir_path)

    def browse_for_working_dir(self):
        """Opens a dialog to select the working directory"""
        # Where you start looking depends on what has been selected
        if self._core_dir_path is None:
            return

        if self.working_path.text() != "":
            start_path = str(self.config_path.parent / self._core_dir_path / self.working_path.text())
        else:
            start_path = str(self.config_path.parent / self._core_dir_path)

        dialog = QtWidgets.QFileDialog.getExistingDirectory
        path = dialog(self, "Select Working Directory", start_path)

        if path:
            path = os.path.relpath(path, str(self.config_path.parent / self._core_dir_path))
            self.working_path.setText(path)


    def browse_for_cocotb_dir(self):
        """Straight copy of browse_for_working_dir. Eventually these options will be genericised
        and code copying will not be required.
        """
        if self._core_dir_path is None:
            return

        if self.cocotb_path.text() != "":
            start_path = str(self.config_path.parent / self._core_dir_path / self.cocotb_path.text())
        else:
            start_path = str(self.config_path.parent / self._core_dir_path)

        dialog = QtWidgets.QFileDialog.getExistingDirectory
        path = dialog(self, "Select CocoTB/pytest directory", start_path)

        if path:
            path = os.path.relpath(path, str(self._core_dir_path))
            self.cocotb_path.setText(path)


    def load_config(self, path: str):
        """Loads an existing config into the editor.

        If it does not exist, creates a new one
        """
        self.config_path = Path(path)
        if not self.config_path.exists():
            dump({}, open(str(self.config_path), "w"))

        with open(str(self.config_path)) as fh:
            config = safe_load(fh.read())
            self.config = config


        self.core_path.setText(config.get("core_dir", ""))
        self.working_path.setText(config.get("working_dir", ""))
        self.top_module.setText(config.get("top_module", ""))
        self.repo_name.setText(config.get("repo_name", ""))
        self.cocotb_path.setText(config.get("cocotb_path", ""))
        self._core_dir_path = self.config_path.parent / self.core_path.text()
        self.rtl.set_core_dir(self._core_dir_path)
        rtl_dirs = config.get("rtl_dirs")
        self.rtl.update(rtl_dirs, self._core_dir_path)
        self.coverage_reasons.open()

        self.parser_args.setPlainText(config.get("parse_args", ""))
        self.verilator_args.setPlainText(config.get("verilator_args", ""))

    def validate(self) -> List[str]:
        """Validates that the input config settings are correct"""
        issues = []

        base_path = self.config_path.parent / self.core_path.text()
        if not base_path.is_dir():
            issues.append(f"{self.core_path.text()} is not a directory")
            return issues

        # TODO should there be a validation scheme here? the directory is meant
        #      to be created...
        #working_path = base_path / self.working_path.text()
        #if not working_path.is_dir() or not self.working_path.text():
        #    issues.append(f"{working_path} is not a directory")

        if not self.top_module.text():
            issues.append("No top level module specified!")

        issues.extend(self.rtl.validate(base_path))
        return issues

    def validate_w_dialog(self):
        issues = self.validate()

        if len(issues) > 0:
            info_message = "\n\n".join(issues)
            QtWidgets.QMessageBox.warning(self, "Issues found in configuration", info_message)
        else:
            QtWidgets.QMessageBox.information(self, "Configuration is good!", "No issues found in configuration")

    def save_cfg(self):
        if len(self.validate()) > 0:
            self.validate_w_dialog()
            return

        self.dump()

    def dump(self):
        self.coverage_reasons.save()

        self.config.update({
            "core_dir": self.core_path.text(),
            "working_dir": self.working_path.text(),
            "top_module": self.top_module.text(),
            "repo_name": self.repo_name.text(),
            "cocotb_path": self.cocotb_path.text(),
            "rtl_dirs": self.rtl.dump(),
            "parse_args": self.parser_args.toPlainText(),
            "verilator_args": self.verilator_args.toPlainText(),
        })

        dump(self.config, open(str(self.config_path), "w"))


class RtlIncludes(QtWidgets.QWidget):
    """Widget to manage RTL file/folder includes
    
    
    What do I need to show?
    Path to file/dir I guess. On validate, I check if it exists
    If it is a file, I add "file": true, to the dictionary that describes it
    Browse button + a remove button
    The add button needs to exist below list of files

    Two widgets, one for a file, and one with add_file and add_dir

    widget for a file has LineEdit, browse button, and remove button, and a recursive
    check box, which is disabled if it's a file
    """
    def __init__(self, parent, config_path):
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("RTL Includes", self)
        self.layout.addWidget(self.label)

        self.add_widget = QtWidgets.QWidget(self)
        self.add_layout = QtWidgets.QHBoxLayout(self.add_widget)
        self.add_file = QtWidgets.QPushButton("Add File", self.add_widget)
        self.add_file.clicked.connect(self._add_file)
        self.add_folder = QtWidgets.QPushButton("Add Folder", self.add_widget)
        self.add_folder.clicked.connect(self._add_folder)

        self.add_layout.addWidget(self.add_file)
        self.add_layout.addWidget(self.add_folder)

        self.layout.addWidget(self.add_widget)

        self.config_path = config_path
        self.core_dir = None

    def set_core_dir(self, core_dir):
        """Required so new configs can appropriately select files based on correct core dir"""
        self.core_dir = core_dir

    def update(self, rtl: List, core_dir):
        """Updates the widgets to display"""
        self.core_dir = Path(core_dir)

        if rtl:
            for path in rtl:
                if Path(path).is_file():
                    self._add_file(file=path)
                else:
                    self._add_folder(folder=path)

    def dump(self):
        """Dump settings as a dictionary"""
        files = []

        for i in range(1, self.layout.count()):
            include = self.layout.itemAt(i).widget()
            if include is not self.add_widget:
                files.append(str(include.include))

        return files

    def _add_file(self, checked=False, file=""):
        """Adds a file to include"""
        rtl_file = RtlPath(self, file, self.core_dir, "file")
        rtl_file.remove.connect(lambda: self.remove(rtl_file))
        rtl_file.path_text.setText(file)
        self.layout.replaceWidget(self.add_widget, rtl_file)
        self.layout.addWidget(self.add_widget)
        if not file:
            rtl_file.browse()

    def _add_folder(self, checked=False, folder=""):
        """Adds a folder to include"""
        rtl_folder = RtlPath(self, folder, self.core_dir, "folder")
        rtl_folder.remove.connect(lambda: self.remove(rtl_folder))
        rtl_folder.path_text.setText(folder)
        self.layout.replaceWidget(self.add_widget, rtl_folder)
        self.layout.addWidget(self.add_widget)
        if not folder:
            rtl_folder.browse()

    def remove(self, include: QtWidgets.QWidget):
        """Removes a file or folder"""
        self.layout.removeWidget(include)
        include.deleteLater()

    def validate(self, _core_dir: Path) -> List[str]:
        """Validates all RTL files"""
        errors = []
        for i in range(1, self.layout.count()):
            include = self.layout.itemAt(i).widget()
            if include is not self.add_widget:
                if include.include == "":
                    errors.append("One or more files/folders does not have a selection")
                    return errors

                path = _core_dir / include.include
                # Check that the file/folder exists
                if not path.exists():
                    # Check globs if we can't find a specific file

                    if len(glob(str(path), recursive=True)) == 0:
                        errors.append(f"{include.include} does not specify at least one file!")

        return errors


class RtlPath(QtWidgets.QWidget):
    """Widget that represents an RTL path to be included"""

    # Signals up that this folder should be removed
    remove = QtCore.Signal()

    def __init__(self, parent, folder: str, core_dir, path_type: str):
        super().__init__(parent)

        self.core_dir = core_dir
        self.path_type = path_type

        # Widget init
        self.layout = QtWidgets.QHBoxLayout(self)

        if path_type == "folder":
            self.label = QtWidgets.QLabel("Folder", self)
        elif path_type == "file":
            self.label = QtWidgets.QLabel("File", self)

        self.path_text = QtWidgets.QLineEdit(folder, self)
        self.recursive_sel = QtWidgets.QCheckBox("Recursive", self)
        self.browse_button = QtWidgets.QPushButton("Browse", self)
        self.remove_button = QtWidgets.QPushButton(self)
        self.remove_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton))

        if Path(folder).name == "**":
            self.recursive_sel.setChecked(True)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.path_text)
        self.layout.setStretch(1, 1)
        self.layout.addWidget(self.recursive_sel)
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(self.remove_button)

        self.browse_button.clicked.connect(self.browse)
        self.remove_button.clicked.connect(self.remove)

        self.recursive_sel.clicked.connect(self.manage_recursive)

    def manage_recursive(self, checked: bool):
        """Slot that ensures glob string is set correctly for a recursive directory."""
        path = Path(self.path_text.text())
        if checked:
            # Add a recursive glob to the end of the string
            if path.name != "**":
                path = path / "**"
        else:
            # Remove a recursive glob at the end of a string
            if path.name == "**":
                path = path.parent

        self.path_text.setText(str(path))

    def browse(self):
        """Browse to replace current folder"""
        if self.path_text.text():
            path = self.path_text.text()
        else:
            path = self.core_dir

        if self.path_type == "folder":
            dialog = QtWidgets.QFileDialog.getExistingDirectory
            path = dialog(self, "Choose RTL Include Directory", str(path))
        elif self.path_type == "file":
            dialog = QtWidgets.QFileDialog.getOpenFileName
            path, _ = dialog(self, "Choose RTL File to add", str(path), "Verilog/SystemVerilog (*.sv *.v)")

        if path:
            path = os.path.relpath(path, str(self.core_dir))
            self.path_text.setText(path)

    @property
    def include(self):
        return self.path_text.text()


# TODO writing this to be as simple as possible to migrate to WIP conf editor system
class OptionList(QtWidgets.QWidget):
    category = "coverage"
    option = "waiver_reasons"


    def __init__(self, parent, get_option: Callable, set_option: Callable):
        self.get_option = partial(get_option, self.category, self.option)
        self.set_option = partial(set_option, self.category, self.option)
        # TODO this all needs to get replaced with the correct infrastructure
        super().__init__(parent)
        self.init_widgets()


    def init_widgets(self):
        self.setLayout(QtWidgets.QVBoxLayout(self))

        self.action_item = QtWidgets.QWidget(self)
        self.action_item.setLayout(QtWidgets.QHBoxLayout(self.action_item))
        # TODO nice icons
        self.clear_items = QtWidgets.QPushButton("Clear", self.action_item)
        self.clear_items.clicked.connect(self.clear_items_action)
        self.add_item = QtWidgets.QPushButton("+", self.action_item)
        self.add_item.clicked.connect(self.add_item_action)
        self.action_item.layout().addWidget(self.clear_items)
        self.action_item.layout().addWidget(self.add_item)

        self.layout().addWidget(self.action_item)


    @property
    def num_items(self) -> int:
        return self.layout().count() - 1


    def add_item_action(self):
        self.layout().replaceWidget(self.action_item, QtWidgets.QLineEdit(self))
        self.layout().addWidget(self.action_item)


    def clear_items_action(self):
        rem_list = []
        for i in range(self.num_items):
            item = self.layout().itemAt(i).widget()
            if item.text() == "":
                rem_list.append(item)

        for rem in rem_list:
            self.layout().removeWidget(rem)
            rem.deleteLater()


    def open(self):
        # Clear all items
        rem_list = []
        for i in range(self.num_items):
            item = self.layout().itemAt(i).widget()
            rem_list.append(item)
        for rem in rem_list:
            self.layout().removeWidget(rem)
            rem.deleteLater()

        items = self.get_option()
        if items is None:
            return
        for item in items:
            # Add back in each item
            self.add_item_action()
            self.layout().itemAt(self.num_items - 1).widget().setText(item)


    def validate(self) -> List[str]:
        # Prune any empty string items
        self.clear_items_action()
        return []


    def save(self):
        # For each item, if str != "", add to list and set this option
        out = []
        for i in range(self.num_items):
            out.append(self.layout().itemAt(i).widget().text())

        self.set_option(out)

