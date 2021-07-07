###############################################################################
# @file pyVerifGUI/tasks/cocotb.py
# @package pyVerifGUI.tasks.cocotb
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief CocoTB/pytest test runner
##############################################################################

from qtpy import QtCore
from typing import List

import subprocess as sp

from pyVerifGUI.tasks.base import Task, is_task
from pyVerifGUI.tasks.worker import Worker

@is_task
class CocoTB(Task):
    _deps = ["cocotb_collect"]
    _name = "cocotb_run"
    _description = "Run cocotb"

    def _run(self):
        try:
            with open(str(self.config.working_dir_path / "cocotb_test_list"), "r") as f:
                tests = [test.strip() for test in f.readlines()]
        except FileNotFoundError:
            # TODO error dialog here
            raise

        if len(tests) == 0:
            raise Exception("No tests!")

        working_dir = self.config.core_dir_path / self.config["cocotb_path"]

        self.worker = TestWorker(self._name, tests, str(working_dir.resolve()))
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)

        self.log_output.emit("Running pytest")
        QtCore.QThreadPool.globalInstance().start(self.worker)

    def callback(self, name, rc, stdout, stderr, time):
        self.run_results.emit(name, rc, stdout, stderr, time)

        self.log_output.emit("pytest finished")

        self.succeed("Finished!", [])

class TestWorker(Worker):
    def fn(self, tests: List[str], working_dir: str):
        # TODO get number of workers from config maybe?

        pytest_cmd = [
            "pytest",
            "-p", "no:terminalreporter",
            "-p", "no:sugar",
            "--hdl-verifgui",
            #"-n", str(n_workers),
            "-n", "2",
        ]
        pytest_cmd.extend(tests)

        self.popen = sp.Popen(pytest_cmd, encoding="utf-8", stdout=sp.PIPE,
                            stderr=sp.PIPE, cwd=working_dir)

        for line in self.popen.stdout.readlines():
            self.log_stdout(line)

        stdout, stderr = self.popen.communicate()
        return (0, stdout, stderr)
