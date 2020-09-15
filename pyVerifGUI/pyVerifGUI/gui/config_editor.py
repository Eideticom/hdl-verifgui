__copyright__ = "Copyright (c) 2020 Eidetic Communications"
__author__ = "David Lenfesty"

# TODO rewrite this whole thing

from qtpy import QtWidgets, QtCore, QtGui
from pathlib import Path
from functools import partialmethod
from yaml import full_load, dump
from typing import List
import os

class ConfigEditorDialog(QtWidgets.QDialog):
    """Dialog for editing config"""
    def __init__(self, parent):
        super().__init__(parent)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.editor = None

    def open(self, config_path = None) -> bool:
        """Opens dialog for editing config"""
        # XXX Would be better to add in proper signalling to change path
        # rather than just rebuilding.
        if self.layout.count():
            self.layout.removeWidget(self.editor)
            self.editor.deleteLater()
        self.editor = ConfigEditor(self, config_path)
        self.editor.save.clicked.connect(self.accept)
        self.layout.addWidget(self.editor)

        return self.exec_()


class ConfigEditor(QtWidgets.QWidget):
    """Widget to create or edit configuration files in a consistent manner"""
    def __init__(self, parent=None, config_path=None):
        super().__init__(parent)

        self.layout = QtWidgets.QGridLayout(self)

        # core dir
        self.core_label = QtWidgets.QLabel("Top level location", self)
        self.core_path = QtWidgets.QLineEdit(self)
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

        # rtl
        self.rtl = RtlIncludes(self, config_path)

        # Extra parser arguments
        # XXX parser should just be integrated, so these should be options
        self.parser_label = QtWidgets.QLabel("Extra parser arguments (optional)", self)
        self.parser_args = QtWidgets.QPlainTextEdit(self)

        # Buttons!
        self.validate_button = QtWidgets.QPushButton("Validate", self)
        self.validate_button.clicked.connect(self.validate_w_dialog)
        self.save = QtWidgets.QPushButton("Save", self)
        self.save.clicked.connect(self.save_cfg)

        #### Layout
        self.layout.setColumnStretch(0, 1)
        self.layout.addWidget(self.core_label, 0, 0)
        self.layout.addWidget(self.core_path, 1, 0)
        self.layout.addWidget(self.browse_core_path, 1, 1)
        self.layout.addWidget(self.working_label, 2, 0)
        self.layout.addWidget(self.working_path, 3, 0)
        self.layout.addWidget(self.browse_working_path, 3, 1)
        self.layout.addWidget(self.top_label, 4, 0)
        self.layout.addWidget(self.top_module, 5, 0)
        self.layout.addWidget(self.repo_label, 6, 0)
        self.layout.addWidget(self.repo_name, 7, 0)
        self.layout.addWidget(self.rtl, 8, 0)
        self.layout.addWidget(self.parser_label, 9, 0)
        self.layout.addWidget(self.parser_args, 10, 0)
        self.layout.addWidget(self.validate_button, 11, 0, 1, 2)
        self.layout.addWidget(self.save, 12, 0, 1, 2)

        if config_path is None:
            dialog = QtWidgets.QFileDialog.getSaveFileName
            config_path, _type = dialog(self,
                                        "Create a configuration file:",
                                        "./",
                                        "YAML Files (*.yaml)")

        self.load_config(config_path)

    def browse_for_core_dir(self):
        """Browse for a directory"""
        start_path = self.core_path.text() if self.core_path.text() != "" else "./"
        dialog = QtWidgets.QFileDialog.getExistingDirectory
        path = dialog(self, "Select Base Directory", start_path)

        # Need to handle it relative to configuration or something
        if path:
            path = os.path.relpath(path, self.config_path.parent)
            self.core_path.setText(path)
            self._core_dir_path = Path(path)
            self.rtl.update({}, self._core_dir_path)

    def browse_for_working_dir(self):
        """Opens a dialog to select the working directory"""
        # Where you start looking depends on what has been selected
        if self._core_dir_path is None:
            return

        if self.core_path.text() == "":
            start_path = "./"
        elif self.working_path.text() != "":
            start_path = self.working_path.text()
        else:
            start_path = self.core_path.text()

        dialog = QtWidgets.QFileDialog.getExistingDirectory
        path = dialog(self, "Select Working Directory", start_path)

        if path:
            path = os.path.relpath(path, str(self._core_dir_path))
            self.working_path.setText(path)

    def load_config(self, path: str):
        """Loads an existing config into the editor.

        If it does not exist, creates a new one
        """
        self.config_path = Path(path)
        if not self.config_path.exists():
            dump({}, open(str(self.config_path), "w"))

        with open(str(self.config_path)) as fh:
            config = full_load(fh.read())
            self.config = config


        self.core_path.setText(config.get("core_dir", ""))
        self.working_path.setText(config.get("working_dir", ""))
        self.top_module.setText(config.get("top_module", ""))
        self.repo_name.setText(config.get("repo_name", ""))
        self._core_dir_path = self.config_path.parent / self.core_path.text()
        rtl_dirs = config.get("rtl_dirs")
        # Only import "proper" rtl dirs
        # XXX could pose a migration issue, given we support more types
        if type(rtl_dirs) is dict:
            self.rtl.update(rtl_dirs, self._core_dir_path)

        self.parser_args.setPlainText(config.get("parse_args", ""))

    def validate(self) -> List[str]:
        """Validates that the input config settings are correct"""
        issues = []

        base_path = self.config_path.parent / self.core_path.text()
        if not base_path.is_dir():
            issues.append(f"{self.core_path.text()} is not a directory")
            return issues

        working_path = base_path / self.working_path.text()
        if not working_path.is_dir() or not self.working_path.text():
            issues.append(f"{working_path} is not a directory")

        if not self.top_module.text():
            issues.append("No top level module specified!")

        issues.extend(self.rtl.validate(self._core_dir_path))
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
        self.config.update({
            "core_dir": self.core_path.text(),
            "working_dir": self.working_path.text(),
            "top_module": self.top_module.text(),
            "repo_name": self.repo_name.text(),
            "rtl_dirs": self.rtl.dump(),
            "parse_args": self.parser_args.toPlainText(),
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

    def update(self, rtl: dict, core_dir):
        """Updates the widgets to display"""
        self.core_dir = Path(core_dir)

        for path in rtl.keys():
            if Path(path).suffix:
                self._add_file(file=path)
            else:
                self._add_folder(folder=path, recursive=rtl[path]["recurse"])

    def dump(self):
        """Dump settings as a dictionary"""
        files = {}

        for i in range(self.layout.count()):
            include = self.layout.itemAt(i).widget()
            if include is not self.add_widget:
                if include is RtlDirectory:
                    recurse = include.recursive_sel.checked()
                else:
                    recurse = False

                files.update({str(include.include): {"recurse": False}})

        return files

    def _add_file(self, checked=False, file=""):
        """Adds a file to include"""
        rtl_file = RtlFile(self, file, self.core_dir)
        rtl_file.remove.connect(lambda: self.remove(rtl_file))
        rtl_file.file_text.setText(file)
        self.layout.replaceWidget(self.add_widget, rtl_file)
        self.layout.addWidget(self.add_widget)
        if not file:
            rtl_file.browse()

    def _add_folder(self, checked=False, folder="", recursive=False):
        """Adds a folder to include"""
        rtl_folder = RtlDirectory(self, folder, False, self.core_dir)
        rtl_folder.remove.connect(lambda: self.remove(rtl_folder))
        rtl_folder.recursive_sel.setChecked(recursive)
        rtl_folder.folder_text.setText(folder)
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
        for i in range(self.layout.count()):
            include = self.layout.itemAt(i).widget()
            try:
                if include is not self.add_widget:
                    if not (self.core_dir / include.include).exists():
                        errors.append(f"{include.include} does not exist!")
            except AttributeError:
                errors.append("RTL file/folder not specified, delete or choose.")

        return errors


class RtlFile(QtWidgets.QWidget):
    """Widget that represents a single RTL file to be included"""

    # Signals up that this folder should be removed
    remove = QtCore.Signal()

    def __init__(self, parent, file: str, core_dir):
        super().__init__(parent)

        self.include = file
        self.core_dir = core_dir

        self.layout = QtWidgets.QHBoxLayout(self)
        self.file_text = QtWidgets.QLineEdit(self.include, self)
        self.browse_button = QtWidgets.QPushButton("Browse", self)
        self.remove_button = QtWidgets.QPushButton(self)
        self.remove_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton))

        self.layout.addWidget(self.file_text)
        self.layout.setStretch(0, 1)
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(self.remove_button)

        self.browse_button.clicked.connect(self.browse)
        self.remove_button.clicked.connect(self.remove)

    def browse(self):
        """Browse for a new file"""
        dialog = QtWidgets.QFileDialog.getOpenFileName
        file, _filter = dialog(self, "Choose RTL File", self.file_text.text(),\
                               "SystemVerilog, Verilog (*.sv *.v)")

        if file:
            file = os.path.relpath(file, str(self.core_dir))
            self.include = file
            self.file_text.setText(file)


class RtlDirectory(QtWidgets.QWidget):
    """Widget that represents an RTL folder to be included"""

    # Signals up that this folder should be removed
    remove = QtCore.Signal()

    def __init__(self, parent, folder: str, recursive: bool, core_dir):
        super().__init__(parent)

        self.include = folder
        self.recursive = recursive
        self.core_dir = core_dir

        # Widget init
        self.layout = QtWidgets.QHBoxLayout(self)
        self.folder_text = QtWidgets.QLineEdit(self.include, self)
        self.recursive_sel = QtWidgets.QCheckBox("Recursive", self)
        self.browse_button = QtWidgets.QPushButton("Browse", self)
        self.remove_button = QtWidgets.QPushButton(self)
        self.remove_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCloseButton))

        self.layout.addWidget(self.folder_text)
        self.layout.setStretch(0, 1)
        self.layout.addWidget(self.recursive_sel)
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(self.remove_button)

        self.browse_button.clicked.connect(self.browse)
        self.remove_button.clicked.connect(self.remove)

    def browse(self):
        """Browse to replace current folder"""
        dialog = QtWidgets.QFileDialog.getExistingDirectory
        path = dialog(self, "Choose RTL Include Directory", self.folder_text.text())

        if path:
            path = os.path.relpath(path, str(self.core_dir))
            self.include = path
            self.folder_text.setText(path)
