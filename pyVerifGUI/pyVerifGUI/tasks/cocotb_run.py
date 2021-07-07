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

import subprocess as sp
from typing import List


from qtpy import QtCore
from oyaml import dump


from pyVerifGUI.tasks.base import Task, is_task
from pyVerifGUI.tasks.worker import Worker

@is_task
class CocoTB(Task):
    _deps = ["cocotb_collect"]
    _name = "cocotb_run"
    _description = "Run cocotb"


    run_began = QtCore.Signal(str, int)
    test_finished = QtCore.Signal()
    testing_complete = QtCore.Signal()


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

        self.worker = TestWorker(self._name, tests, str(working_dir.resolve()), self.config)
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)
        self.worker.signals.run_began.connect(self.run_began)
        self.worker.signals.test_finished.connect(self.test_finished)
        self.worker.signals.testing_complete.connect(self.testing_complete)

        self.log_output.emit("Running pytest")
        QtCore.QThreadPool.globalInstance().start(self.worker)

    def callback(self, name, rc, stdout, stderr, time):
        self.run_results.emit(name, rc, stdout, stderr, time)

        self.log_output.emit("pytest finished")

        self.succeed("Finished!", [])

class TestWorker(Worker):
    foo = QtCore.Signal()
    def fn(self, tests: List[str], working_dir: str, config):
        # TODO get number of workers from config maybe?
        self.signals.run_began.emit("CocoTB", len(tests))
        status = {}

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
            line = line.rstrip().split(',')
            if line[0] != "REPORT":
                continue

            nodeid = line[1]
            if line[2] == "setup":
                status[nodeid] = {"status": "started"}
            elif line[2] == "call":
                status[nodeid] = {"status": line[3], "time": line[4]}
            else:
                continue

            with open(str(config.working_dir_path / "cocotb_test_status.yaml"), "w") as f:
                dump(status, f)

            if line[2] == "call":
                self.signals.test_finished.emit()

        stdout, stderr = self.popen.communicate()
        self.signals.testing_complete.emit()
        return (0, stdout, stderr)
