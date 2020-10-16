__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from qtpy import QtCore, QtWidgets
from yaml import full_load
from pathlib import Path
import shutil

from pyVerifGUI.parsers import parse_verilator_error

from .runners import SVParseWorker
from .base import Task, TaskFinishedDialog, task_names, TaskFailedDialog
from .lint import LintTask


class ParseTask(Task):
    _deps = []
    _running = False
    _name = task_names.parse
    _description = "SystemVerilog Design Parser (pySVparser)"

    def run(self, is_last=True):
        """Run parser task"""
        self.throw_dialog = is_last
        self.copy_dialog = CopyOutputsDialog(self.config)

        # Attempt to copy previous build
        if self.copy_dialog.askForCopy():
            self.log_output.emit("RTL copied from previous build")
            self.finished = True
            self.config.dump_build()
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
            self._running = False

            self.status = "failed"
            self.finished = True
            self.config.dump_build()
            TaskFailedDialog("Parsing",
                             "Parsing failed! Check command outputs").exec_()
            self.task_result.emit([])
            return

        self.finished = True
        self.taskFinish()

    def taskFinish(self):
        """Cleanup"""
        dialog = TaskFinishedDialog(self._name)
        tasks = []

        tasks.append(task_names.lint)
        self.log_output.emit("Parsing succeeded!")
        if self.throw_dialog:
            dialog.addNextTask(task_names.lint)
            msg = "Parsing succeeded!"
            tasks.extend(dialog.run(msg))

        self.status = "passed"

        self.task_result.emit(tasks)
        self._running = False
        self.config.dump_build()


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
            config = full_load(
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
