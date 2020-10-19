###############################################################################
# @file pyVerifGUI/tasks/lint.py
# @package pyVerifGUI.tasks.lint
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Verilator linting task
##############################################################################

from qtpy import QtCore

from pyVerifGUI.parsers import parse_verilator_output

from .runners import LinterWorker
from .base import Task, TaskFinishedDialog, task_names, TaskFailedDialog


class LintTask(Task):
    _deps = [task_names.parse]
    _running = False
    _name = task_names.lint
    _description = "SystemVerilog Linter (Verilator)"

    def __init__(self, config):
        super().__init__(config)

        self.dialog = TaskFinishedDialog(self._name)

    def run(self, is_last=True):
        """Runs linter task"""
        self.throw_dialog = is_last

        self.worker = LinterWorker(self._name, self.config)

        self.worker.signals.result.connect(self.callback)
        self.worker.signals.result.connect(self.run_results)
        self.worker.signals.stdout.connect(self.run_stdout)

        self.log_output.emit("Linting design...")
        QtCore.QThreadPool.globalInstance().start(self.worker)
        self._running = True

    def callback(self, name: str, rc: int, stdout: str, stderr: str,
                 time: float):
        """Handles linting cleanup"""
        del name, stdout, stderr, time
        if rc == -42:
            self._running = False
            self.finished = False
            self.status = "failed"
            self.config.dump_build()
            TaskFailedDialog(
                "Linter",
                "An exception was thrown while linting! Check run outputs"
            ).exec_()
            self.task_result.emit([])
            return

        self._running = False
        self.finished = True
        self.status = "passed"
        self.log_output.emit("Linting finshed!")

        tasks = self.dialog.run("Linting Finished!")
        self.task_result.emit(tasks)
        self.config.dump_build()
