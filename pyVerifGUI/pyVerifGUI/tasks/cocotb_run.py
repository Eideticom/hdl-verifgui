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
from pathlib import Path
import subprocess as sp
from typing import List
import time
import os


from qtpy import QtCore
from oyaml import dump, load, Loader


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

        if rc >= 0:
            self.succeed("Finished!", [])
        else:
            self.fail("Test run incomplete!")

class TestWorker(Worker):
    foo = QtCore.Signal()
    def fn(self, tests: List[str], working_dir: str, config):
        current_status_path: Path = config.working_dir_path / "cocotb_test_status.yaml"
        if current_status_path.exists():
            with open(str(current_status_path), "r") as f:
                status = load(f, Loader=Loader)
        else:
            status = {}

        self.signals.run_began.emit("CocoTB", len(tests))
        run_start = time.time()
        test_history_path = config.working_dir_path / "cocotb_test_history.yaml"

        # Only run unfinished tests
        to_run = []
        for test in tests:
            if test in status and status[test]["status"] == "passed":
                continue

            to_run.append(test)

        # If everything passed, just re-run them all anyways
        if len(to_run) == 0:
            to_run = tests

        pytest_cmd = [
            "pytest",
            "-p", "no:terminalreporter",
            "-p", "no:sugar",
            "--hdl-verifgui",
            "-n", str(config.thread_count),
        ]
        env = os.environ.copy()
        env["GUI_TEST"] = "True"
        env["LOGLEVEL"] = "WARNING"
        extra_params = config.working_dir_path / "cocotb_extra_params.yaml"
        if extra_params.exists():
            with open(str(extra_params)) as f:
                new_env = load(f, Loader=Loader)
                for opt in new_env:
                    new_env[opt] = str(new_env[opt])
                env.update(new_env)

        self.log_stdout(" ".join(pytest_cmd) + " " + " ".join(f"\"{test}\"" for test in to_run))
        pytest_cmd.extend(to_run)
        self.popen = sp.Popen(
            pytest_cmd,
            encoding="utf-8",
            stdout=sp.PIPE, stderr=sp.PIPE,
            cwd=working_dir,
            env=env,
        )

        for line in self.popen.stdout:
            self.log_stdout(line)
            line = line.rstrip().split(',')
            if line[0] != "REPORT":
                continue

            nodeid = line[1]
            if line[2] == "setup":
                status[nodeid] = {
                    "status": "started",
                    "run_start": int(run_start),
                    "start_time": int(time.time()),
                }
            elif line[2] == "call":
                status[nodeid] = {"status": line[3], "time": float(line[4])}

                # Write to "long-term" test status
                if test_history_path.exists():
                    with open(str(test_history_path)) as f:
                        test_history = load(f, Loader=Loader)
                else:
                    test_history = {}

                # Save specific test instance
                _test = test_history.get(nodeid, {})
                _test[status[nodeid]['run_start']] = status[nodeid]
                test_history[nodeid] = _test

                # TODO is there any way to/is it faster to modify in place?
                with open(str(test_history_path)) as f:
                    dump(test_history, test_history_path)

            else:
                continue

            with open(str(config.working_dir_path / "cocotb_test_status.yaml"), "w") as f:
                dump(status, f)

            # TODO add another more general update signal?
            #if line[2] == "call" or line[2] == "setup":
            if line[2] == "call":
                self.signals.test_finished.emit()
                # Sometimes the signals don't propogate fast enough to update nicely
                time.sleep(0.05)

        # Check for incomplete tests
        test_failed = False
        for test in status:
            if status[test]["status"] != "passed":
                test_failed = True
                break

        stdout, stderr = self.popen.communicate()
        self.signals.testing_complete.emit()
        if test_failed:
            if self.popen.returncode < 0:
                rc = self.popen.returncode
            else:
                rc = -1
        else:
            rc = self.popen.returncode
        return (rc, stdout, stderr)
