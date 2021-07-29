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
from qtpy import QtWidgets, QtCore
from typing import List, Any, MutableMapping, Optional
from oyaml import safe_load, dump, load, Loader
from pathlib import Path
from glob import glob
import os


class ConfigStorage(MutableMapping):
    def __init__(self, storage: dict):
        self.storage = storage


    def __getitem__(self, key):
        return self.storage[key]


    def __setitem__(self, key, value):
        self.storage[key] = value


    def __delitem__(self, key):
        self.storage.__delitem__(key)


    def __iter__(self):
        return self.storage.__iter__()


    def __len__(self):
        return self.storage.__len__()


    def update(self, values):
        self.storage.update(values) 


# TODO rework this widget so exception passing out of a constructor is not required.
class ConfigNotSelected(Exception):
    """Exception for passing errors up out of editor object"""


# TODO will need to catch these errors and print what class failed to initialize
# TODO need to provide a way to raise an issue when openning config, perhaps specific exceptions in open()?
class ConfigEditorOption(QtWidgets.QWidget):
    """Option "plugin" to use to extend the configuration editor.
    Several examples are present in config_editor.py, that are already used in the configuration.

    Use `register_config_option` as a decorator to add an option to the configuration editor.
    Provide the decorator with a category and option, which will be used to sort the items, as
    shown below (breadth-first alphabetical order):

    main_option_1: value
    main_option_2: value
    category:
      option: value
    category2:
      option: value

    Any ConfigEditorOption is passed the value under its specified category/value pair.
    Options with category "Main" exist on the top level.
    """
    # Signal to emit whenever data is updated. Triggers a `save` call and updates
    # the cached config
    updated = QtCore.Signal()


    @property
    def category(self) -> str:
        """Category to place option under - set by register_config_option decorator"""
        raise NotImplementedError


    @property
    def option(self) -> str:
        """Option name - set by register_config_option decorator"""
        raise NotImplementedError


    def init_widgets(self):
        """Subclass initialization, do *NOT* re-impliment init, instead use this"""
        raise NotImplementedError

    def open(self):
        """Called when a configuration is opened. Expected to fill data in to widgets.

        Do so safely, catch any exceptions and default to empty
        """
        raise NotImplementedError

    def validate(self) -> List[str]:
        """Called when running validate step.

        Returns list of issues with the configuration

        Only options under the "Main" category will be errors, all else will be treated as warnings
        """
        raise NotImplementedError

    def save(self):
        """Called when save gets entered. Should save to the config dictionary.

        This is required because some widgets don't have a handy built in way to do this, just
        the way they are designed.
        """
        raise NotImplementedError

    def __init__(self, parent, cfg: ConfigStorage):
        super().__init__(parent)
        self.config = cfg
        self.init_widgets()


    def check_core_dir(self, dialog: bool = False) -> Optional[str]:
        """Check if core dir exists, also can raise dialog box if it does not."""
        core_dir = self.config["main"].get("core_dir", None)
        if core_dir is None and dialog:
            QtWidgets.QMessageBox.warning(
                self,
                "Core directory not specified!",
                "The core directory is not configured, and is necessary for all other paths.")

        return core_dir


    @property
    def core_dir(self) -> Optional[Path]:
        core_dir = self.config["main"].get("core_dir", None)
        if core_dir is not None:
            return Path(self.config["config_path"]).parent / core_dir

        return None


    def get_option(self) -> Optional[Any]:
        if self.category in self.config:
            if self.option in self.config[self.category]:
                return self.config[self.category][self.option]

        return None


    def set_option(self, value: Any):
        if not self.category in self.config:
            self.config[self.category] = {}

        self.config[self.category][self.option] = value


config_options: List[ConfigEditorOption] = []
# TODO migrate other plugins to a similar system... how did I not think of this before?
#      Way simpler to register and go through a list than search through every import...
# TODO better exception
def register_config_option(category: str, option: str):
    """Decorator to register class as a configuration option"""
    def wrapper(opt: ConfigEditorOption):
        # TODO unsure why this doesn't work
        #if not isinstance(opt, ConfigEditorOption):
        #    raise Exception("Attempted to register a configuration option that is not a ConfigEditorOption")

        config_options.append(opt)
        opt.category = category
        opt.option = option
        return opt

    return wrapper


class ConfigEditorDialog(QtWidgets.QDialog):
    """Dialog for editing config"""
    def __init__(self, parent):
        super().__init__(parent)
        # TODO this seems to get called twice, why is that?
        self.setLayout(QtWidgets.QVBoxLayout(self))
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.layout().addWidget(self.scroll_area)
        self.cfg_widget = QtWidgets.QWidget(self.scroll_area)
        self.cfg_widget.setLayout(QtWidgets.QVBoxLayout(self.cfg_widget))
        self.categories = []

        self.config = ConfigStorage({})
        # Sort options alphabetically, "main" first however
        self.options = {"main": {}}
        for opt in [opt for opt in config_options if opt.category == "main"]:
            self.options["main"][opt.option] = opt
        for opt in sorted([opt for opt in config_options if opt.category != "main"], key=lambda key: key.category):
            if opt.category not in self.options:
                self.options[opt.category] = {}
            self.options[opt.category][opt.option] = opt

        for cat in self.options:
            category = QtWidgets.QWidget(self.cfg_widget)
            self.cfg_widget.layout().addWidget(category)
            category.setLayout(QtWidgets.QVBoxLayout(category))
            # TODO maybe nicer widget with a line or something?
            if cat != "main":
                category.layout().addWidget(QtWidgets.QLabel(cat, category))
            for opt in sorted(self.options[cat], key=lambda key: self.options[cat][key].option):
                _opt = self.options[cat][opt](category, self.config)
                category.layout().addWidget(_opt)
                self.options[cat][opt] = _opt
                _opt.updated.connect(self.save_options)

            self.categories.append(category)

        # See function docs, but the layout of the widget has to be set before
        # you can add the widget to the scroll area. If you put this before here
        # nothing will be visible.
        self.scroll_area.setWidget(self.cfg_widget)


        # Management Buttons
        self.buttons = QtWidgets.QWidget(self)
        self.buttons.setLayout(QtWidgets.QHBoxLayout(self.buttons))
        self.validate = QtWidgets.QPushButton("Validate", self.buttons)
        self.validate.clicked.connect(self.validate_action)
        self.save = QtWidgets.QPushButton("Save", self.buttons)
        self.save.clicked.connect(self.save_action)
        self.buttons.layout().addWidget(self.validate)
        self.buttons.layout().addWidget(self.save)

        self.layout().addWidget(self.buttons)


    def display_errors(self, errors: List[str]):
        title = f"{len(errors)} found, please correct them"
        body = "\n".join([f"- {err}" for err in errors])
        QtWidgets.QMessageBox.warning(self, title, body)


    def validate_action(self):
        errors = self._validate()
        if len(errors) > 0:
            self.display_errors(errors)


    def _validate(self) -> List[str]:
        errors = []
        for cat in self.options.values():
            for opt in cat.values():
                errors.extend(opt.validate())

        return errors


    def save_action(self):
        """Save configuration to disk"""
        errors = self._validate()
        if len(errors) == 0:
            config_path = self.config["config_path"]
            self.config.__delitem__("config_path")
            with open(str(config_path), 'w') as f:
                dump(self.config.storage, f)
            self.config["config_path"] = config_path
        else:
            self.display_errors(errors)


    def save_options(self):
        """Ensure options are updated in cache"""
        for cat in self.options.values():
            for opt in cat.values():
                opt.save()


    def open(self, config_path = None) -> bool:
        """Opens dialog for editing config

        Returns True when dialog succeeds
        """
        # TODO evaluate status of dialog
        self.open_config(config_path)
        self.exec_()
        return False


    def open_config(self, config_path = None):
        # TODO there is no error handling here...
        if config_path is not None:
            with open(str(config_path)) as f:
                # TODO maybe hide this behind a seperate Config object or something,
                # so I can pass it once and update it more easily
                self.config.storage = load(f, Loader=Loader)

            self.config["config_path"] = config_path
            for cat in self.options.values():
                for opt in cat.values():
                    opt.open()


class TextOption(ConfigEditorOption):
    @property
    def _label(self) -> str:
        raise NotImplementedError


    @property
    def _optional(self) -> bool:
        return True


    def init_widgets(self):
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.label = QtWidgets.QLabel(self._label, self)
        self.text = QtWidgets.QLineEdit(self)
        self.layout().addWidget(self.label)
        self.layout().addWidget(self.text)


    def open(self):
        value = self.get_option()
        if value is not None:
            self.text.setText(value)
        else:
            self.text.setText("")


    def save(self):
        self.set_option(self.text.text())


    def validate(self) -> List[str]:
        if not self._optional and len(self.text.text()) == 0:
            return [f"{self._label} must contain some value!"]

        return []


class FolderOption(ConfigEditorOption):
    @property
    def _force_browse(self) -> bool:
        """Optional attribute to set which will force the user to use the browse button,
        i.e. make the text field read-only
        """
        return False

    @property
    def _label(self) -> str:
        """Attribute to set label text, required for implementation"""
        raise NotImplementedError

    @property
    def _dialog_title(self) -> str:
        raise NotImplementedError

    def init_widgets(self):
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().addWidget(QtWidgets.QLabel(self._label, self))

        self.path = QtWidgets.QLineEdit(self)
        self.path.setReadOnly(self._force_browse)
        self.layout().addWidget(self.path)

        self.browse = QtWidgets.QPushButton("Browse", self)
        self.browse.clicked.connect(self.browse_action)
        self.layout().addWidget(self.browse)


    def browse_action(self):
        core_dir = self.check_core_dir()
        if core_dir is None:
            return

        if self.path.text():
            start_path = self.path.text()
        else:
            start_path = self.core_dir

        dir = QtWidgets.QFileDialog.getExistingDirectory(self, self._dialog_title, str(start_path))
        if dir:
            dir = Path(dir).relative_to(core_dir)

            self.path.setText(str(dir))
            self.updated.emit()


    def open(self):
        value = self.get_option()
        if value is not None:
            self.path.setText(value)
        else:
            self.path.setText("")


    def save(self):
        txt = self.path.text()
        if len(txt) > 0:
            self.set_option(txt)


    def validate(self) -> List[str]:
        core_dir = self.core_dir
        if core_dir is not None:
            if self.category not in self.config:
                return []
            if self.option not in self.config[self.category]:
                return []

            dir: Path = core_dir / self.config[self.category][self.option]
            if not dir.exists():
                return [f"[{self.category}] {self.option}: directory does not exist!"]
            if not dir.is_dir():
                return [f"[{self.category}] {self.option}: not a directory!"]

        return []


class OptionList(ConfigEditorOption):
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
        self.updateGeometry()


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


class RtlIncludes(ConfigEditorOption):
    """Widget to manage file/folder includes"""
    def init_widgets(self):
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


    def open(self):
        pass


    def validate(self):
        pass


    def save(self):
        pass

    def set_core_dir(self, core_dir):
        """Required so new configs can appropriately select files based on correct core dir"""
        self.core_dir = core_dir

    def update(self, rtl: List, core_dir):
        """Updates the widgets to display"""
        self.core_dir = Path(core_dir)

        if rtl:
            for path in rtl:
                self._add_file(file=path)

    def dump(self):
        """Dump settings as a dictionary"""
        files = []

        for i in range(self.layout.count()):
            include = self.layout.itemAt(i).widget()
            if include is not self.add_widget:
                files.append(str(include.include))

        return files

    def _add_file(self, checked=False, file=""):
        """Adds a file to include"""
        rtl_file = RtlPath(self, file, self.config_path.parent / self.core_dir)
        rtl_file.remove.connect(lambda: self.remove(rtl_file))
        rtl_file.path_text.setText(file)
        self.layout.replaceWidget(self.add_widget, rtl_file)
        self.layout.addWidget(self.add_widget)
        if not file:
            rtl_file.browse(path_type="file")

    def _add_folder(self, checked=False, folder=""):
        """Adds a folder to include"""
        rtl_folder = RtlPath(self, folder, self.config_path.parent / self.core_dir)
        rtl_folder.remove.connect(lambda: self.remove(rtl_folder))
        rtl_folder.path_text.setText(folder)
        self.layout.replaceWidget(self.add_widget, rtl_folder)
        self.layout.addWidget(self.add_widget)
        if not folder:
            rtl_folder.browse(path_type="folder")

    def remove(self, include: QtWidgets.QWidget):
        """Removes a file or folder"""
        self.layout.removeWidget(include)
        include.deleteLater()

    def validate(self, _core_dir: Path) -> List[str]:
        """Validates all RTL files"""
        errors = []
        for i in range(self.layout.count()):
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

    def __init__(self, parent, folder: str, core_dir):
        super().__init__(parent)

        self.core_dir = core_dir

        # Widget init
        self.layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel("Folder", self)
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

    def browse(self, path_type: str = "folder"):
        """Browse to replace current folder"""
        if self.path_text.text():
            path = self.path_text.text()
        else:
            path = self.core_dir

        if path_type == "folder":
            dialog = QtWidgets.QFileDialog.getExistingDirectory
            path = dialog(self, "Choose RTL Include Directory", str(path))
        elif path_type == "file":
            dialog = QtWidgets.QFileDialog.getOpenFileName
            path, _ = dialog(self, "Choose RTL File to add", str(path), "Verilog/SystemVerilog (*.sv *.v)")

        if path:
            path = os.path.relpath(path, str(self.core_dir))
            self.path_text.setText(path)

    @property
    def include(self):
        return self.path_text.text()


##############################################################################
# Default Config Options
@register_config_option("main", "core_dir")
class CoreDir(FolderOption):
    """Special configuration option, lots of things overriden from the general
    defaults because most things are meant to be relative to this option.
    """
    # TODO what even do I name things
    _force_browse = True
    _label = "Core Directory"
    _dialog_title = "Project Directory"


    def browse_action(self):
        """Overriden for special core_dir case"""
        if self.path.text():
            start_path = self.path.text()
        else:
            start_path = self.config["config_path"]

        dir = QtWidgets.QFileDialog.getExistingDirectory(self, self._dialog_title, start_path)
        if dir:
            dir = Path(dir).relative_to(Path(self.config["config_path"]).absolute().parent)
            self.path.setText(str(dir))
            self.updated.emit()


    def validate(self) -> List[str]:
        """Overriden for special core_dir case"""
        dir = Path(self.config[self.category][self.option])
        if not dir.exists():
            return [f"[{self.category}] {self.option}: directory does not exist!"]
        if not dir.is_dir():
            return [f"[{self.category}] {self.option}: not a directory!"]

        return []


@register_config_option("main", "working_dir")
class WorkingDir(FolderOption):
    _label = "Working Directory"
    _dialog_title = "Choose a working directory:"


@register_config_option("main", "top_module")
class TopModule(TextOption):
    _label = "Top Module"
    _optional = False


@register_config_option("main", "repo_name")
class RepoName(TextOption):
    _label = "Repository Name"
    _optional = True


@register_config_option("cocotb", "working_dir")
class CocoTBWorkingDir(FolderOption):
    _label = "CocoTB Base Directory"
    _dialog_title = "Choose base CocoTB directory:"


@register_config_option("parser", "extra_args")
class ParserArgs(TextOption):
    _label = "Extra SV Parser Arguments"
    _optional = True


@register_config_option("linter", "extra_args")
class VerilatorLinterArgs(TextOption):
    _label = "Extra Verilator Linter Arguments"
    _optional = True


@register_config_option("coverage", "waiver_reasons")
class WaiverReasons(OptionList):
    pass

