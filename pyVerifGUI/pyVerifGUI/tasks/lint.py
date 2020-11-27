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
from .base import Task, is_task, TaskFinishedDialog, task_names, TaskFailedDialog


@is_task
class LintTask(Task):
    _deps = [task_names.parse]
    _name = task_names.lint
    _description = "SystemVerilog Linter (Verilator)"

    def __init__(self, config):
        super().__init__(config)

        self.dialog = TaskFinishedDialog(self._name)

    def _run(self):
        """Runs linter task"""
        self.worker = LinterWorker(self._name, self.config)

        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)

        self.log_output.emit("Linting design...")
        QtCore.QThreadPool.globalInstance().start(self.worker)

    def callback(self, name: str, rc: int, stdout: str, stderr: str,
                 time: float):
        """Handles linting cleanup"""
        # Output any stderr to logging
        self.run_results.emit(name, rc, stdout, stderr, time)

        if rc == -42:
            self.fail("An exception was thrown while linting! Check run outptus")
            return

        self.log_output.emit("Linting finshed!")
        self.succeed("Linting Finished!", [])
