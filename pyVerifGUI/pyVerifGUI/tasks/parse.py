###############################################################################
# @file pyVerifGUI/tasks/parse.py
# @package pyVerifGUI.tasks.parse
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief rSVParser SystemVerilog parser task
##############################################################################

from qtpy import QtCore, QtWidgets
from typing import Optional, List
from oyaml import safe_load
from pathlib import Path
import subprocess as sp
import shutil

from pyVerifGUI.tasks.base import Task, is_task, task_names
from pyVerifGUI.tasks.worker import Worker

from pyVerifGUI.gui.config import Config


@is_task
class ParseTask(Task):
    _deps = []
    _running = False
    _name = task_names.parse
    _description = "SystemVerilog Design Parser (pySVparser)"

    def _run(self):
        """Run parser task"""
        self.copy_dialog = CopyOutputsDialog(self.config)

        # Attempt to copy previous build
        if self.copy_dialog.askForCopy():
            self.log_output.emit("RTL copied from previous build...")
            self.taskFinish()
        else:
            self.worker = SVParseWorker(self._name, self.config)

            self.worker.signals.result.connect(self.callback)
            self.worker.signals.result.connect(self.run_results)
            self.worker.signals.stdout.connect(self.run_stdout)

            self.log_output.emit("Parsing RTL...")
            QtCore.QThreadPool.globalInstance().start(self.worker)
            self._running = True

    def callback(self, tag: str, rc: int, stdout: str, stderr: str,
                 time: float):
        """Callback to finish parsing"""
        del tag, stdout, time
        if rc != 0:
            self.log_output.emit("Parsing failed...")
            self.fail("Parsing failed! Check command outputs")
            return

        self.taskFinish()

    def taskFinish(self):
        """Cleanup"""
        self.log_output.emit("Parsing succeeded!")
        self.succeed("Parsing succeeded!", [task_names.lint])


def create_rtlfiles_list(top_module, sv_rtl_fileslist_filename, sv_cfg_data):
    if not top_module in sv_cfg_data['sv_hierarchy']:
        return f"<ERROR> '{top_module}' not found in hiearchy tree (sv_hierarchy.yaml)"

    htree = sv_cfg_data['sv_hierarchy'][top_module]['tree']

    def get_modules(blk_dict: dict):
        modules = list(blk_dict.keys())
        for branch in blk_dict.values():
            modules.extend(get_modules(branch))

        return modules

    modules = get_modules(htree)
    files_lst = []
    for pkg_data in sv_cfg_data['sv_packages'].values():
        if pkg_data['path'] not in files_lst:
            files_lst.append(pkg_data['path'])

    for if_data in sv_cfg_data['sv_interfaces'].values():
        if if_data['path'] not in files_lst:
            files_lst.append(if_data['path'])

    for mdl_name in modules:
        try:
            mdl = sv_cfg_data['sv_modules'][mdl_name]
            if mdl['path'] not in files_lst:
                files_lst.append(mdl['path'])
        except KeyError:
            # This happens when external modules are used, such as FPGA intrinsics
            pass

    posix_pathlst = [Path(path).as_posix() for path in files_lst]
    with Path(sv_rtl_fileslist_filename).open('w') as fptr:
        fptr.write("\n".join(posix_pathlst))


def get_extra_args(args: Optional[str]) -> List:
    """Pares out extra args and add to a string"""
    if args is not None:
        args = args.strip()
        if args:
            return args.strip().split(" ")

    return []


class SVParseWorker(Worker):
    def fn(self, stdout, config: Config):
        """Run the SystemVerilog parser and save its output to the build
        directory
        """
        # Check if rSVParser exists first
        try:
            thing = sp.run(["rSVParser", "-h"], capture_output=True)
            self.cmd_list = ["rSVParser"]
        except FileNotFoundError:
            return (
                -1, "",
                "rSVParser not found! Please ensure it is installed and in your PATH."
            )

        self.cmd_list = ["rSVParser", config.top_module, "--top_module"]
        for path in config.rtl_dir_paths:
            self.cmd_list.extend(["--include", str(path)])

        parse_args = config.config.get("parse_args", None)
        self.cmd_list.extend(get_extra_args(parse_args))
        self.display_cmd()

        try:
            self.popen = sp.Popen(self.cmd_list,
                                  stdout=sp.PIPE,
                                  stderr=sp.PIPE,
                                  cwd=config.working_dir_path)
        except Exception as exc:
            return (-1, "", str(exc))
        returncode, stdout = self.emit_stdout("parser")
        _, stderr = self.popen.communicate()

        if returncode != 0:
            # Necessary, because when the parser fails, the required files often do not exist
            return (returncode, stdout, stderr.decode())

        # Copy output to build directory
        working_parse_path = config.build_path / f"sv_{config.top_module}"

        # Generate list of files for linter to use
        modules = safe_load(open(str(working_parse_path / "sv_modules.yaml")))
        hierarchy = safe_load(
            open(str(working_parse_path / "sv_hierarchy.yaml")))
        packages = safe_load(open(str(working_parse_path /
                                      "sv_packages.yaml")))
        interfaces = safe_load(
            open(str(working_parse_path / "sv_interfaces.yaml")))
        sv_cfg = {
            "sv_modules": modules,
            "sv_hierarchy": hierarchy,
            "sv_packages": packages,
            "sv_interfaces": interfaces,
        }
        error = create_rtlfiles_list(config.top_module,
                                  str(config.build_path / "rtlfiles.lst"), sv_cfg)
        if error:
            return (-1, "", error)

        return (returncode, stdout, stderr.decode())



class CopyOutputsDialog(QtWidgets.QDialog):
    """Dialog to ask (and act) if the user wants to copy an older parse job."""
    def __init__(self, config):
        super().__init__()
        self.setModal(True)
        self.config = config

        self.layout = QtWidgets.QVBoxLayout(self)

        self.copy_path = ""
        self.use_build = True

        #### Initial view
        msg = "Parsing may take a few minutes, do you want to copy a previous run?"
        self.msg = QtWidgets.QLabel(msg, self)

        self.buttons = QtWidgets.QDialogButtonBox(self)
        self.yes = QtWidgets.QPushButton("Yes, select build to copy from",
                                         self)
        self.from_dir = QtWidgets.QPushButton(
            "Yes, select directory to copy from", self)
        self.no = QtWidgets.QPushButton("No")
        self.buttons.addButton(self.yes, self.buttons.AcceptRole)
        self.buttons.addButton(self.from_dir, self.buttons.AcceptRole)
        self.buttons.addButton(self.no, self.buttons.RejectRole)

        self.yes.clicked.connect(self.chooseBuild)
        self.from_dir.clicked.connect(self.chooseDir)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.msg)
        self.layout.addWidget(self.buttons)

        #### Build select view
        self.build_label = QtWidgets.QLabel(
            "Please select a build to copy from", self)
        self.build_label.hide()
        self.build_select = QtWidgets.QComboBox(self)
        self.build_select.hide()
        self.build_buttons = QtWidgets.QDialogButtonBox(self)
        self.build_buttons.addButton(self.build_buttons.Ok)
        self.build_buttons.addButton(self.build_buttons.Cancel)
        self.build_buttons.hide()

        self.build_buttons.accepted.connect(self.copyFiles)
        self.build_buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.build_label)
        self.layout.addWidget(self.build_select)
        self.layout.addWidget(self.build_buttons)

    def askForCopy(self) -> bool:
        """Opens dialog and proceeds with copying if selected

        returns True if files have been copied
        """
        # ensure correct view
        self.msg.show()
        self.buttons.show()
        self.build_label.hide()
        self.build_select.hide()
        self.build_buttons.hide()
        return self.exec_()

    def chooseBuild(self):
        """Pivots dialog to select a valid build to copy from"""
        # change view
        self.use_build = True
        self.msg.hide()
        self.buttons.hide()
        self.build_label.show()
        self.build_select.show()
        self.build_buttons.show()

        # Find builds which have parsing enabled
        for build in self.config.builds:
            config = safe_load(
                open(str(self.config.builds_path / build /
                         "build_status.yaml")))
            if config[task_names.parse]:
                self.build_select.addItem(build)

    def chooseDir(self):
        """Just opens a new dialog to select a folder"""
        self.use_build = False
        get_dir = QtWidgets.QFileDialog.getExistingDirectory
        self.copy_path = get_dir(self, "Select Directory to Load Parsed Files")

        if self.copy_path == "":
            self.reject()
            return

        self.config.log_output.emit(
            f"Loading parsed files from {self.copy_path}")
        self.copyFiles()

    def copyFiles(self):
        """Copies parser files from selected build"""

        # Copy parser files over
        if self.use_build:
            # Reject if no build was selected
            if self.build_select.currentText() == "":
                self.reject()
            build = self.build_select.currentText()
        else:
            build = Path(self.copy_path).resolve()
        parse_dir = f"sv_{self.config.top_module}"
        prev_parse_path = self.config.builds_path / build / parse_dir
        new_parse_path = self.config.build_path / parse_dir
        if new_parse_path.exists():
            shutil.rmtree(str(new_parse_path))

        try:
            shutil.copytree(str(prev_parse_path), str(new_parse_path))
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Copy Build Failed!", str(exc))
            self.reject()
            return

        # Copy rtlfiles list over
        prev_list = self.config.builds_path / build / "rtlfiles.lst"
        new_list = self.config.build_path / "rtlfiles.lst"
        try:
            shutil.copyfile(prev_list, new_list)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Copy Build Failed!", str(exc))
            self.reject()
            return

        self.accept()
