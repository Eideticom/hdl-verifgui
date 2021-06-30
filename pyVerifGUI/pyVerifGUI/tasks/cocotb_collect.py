###############################################################################
# @file pyVerifGUI/tasks/cocotb_collect.py
# @package pyVerifGUI.tasks.cocotb
# @author David Lenfesty
# @copyright Copyright (c) 2021. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Collect CocoTB/pytest testcases
##############################################################################
from dataclasses import dataclass
from pathlib import Path
from qtpy import QtCore
from typing import Dict
import time
import re

import subprocess as sp
from oyaml import dump

from pyVerifGUI.tasks.base import Task, is_task
from pyVerifGUI.tasks.worker import Worker
from pyVerifGUI.tasks.cocotb import *

@dataclass
class Test:
    # nodeid = path::test
    path: str
    test: str

    # Do we have these markers?
    coverage: bool
    regression: bool

def test_from_line(line: str) -> Test:
    """Parse line and generate a test object"""
    fields = line.split(',')
    nodeid = fields[0].split('::')
    return Test(nodeid[0], nodeid[1], fields[1], fields[2])


@is_task
class CocoTBCollect(Task):
    _deps = []
    _name = "cocotb_collect"
    _description = "Collect all available CocoTB tests"

    def _run(self):
        path = self.config.config.get("cocotb_path", None)
        if path is None or len(path) == 0:
            self.fail("No path configured for cocotb!")
            return
        path = self.config.core_dir_path / path
        if not path.exists():
            self.fail(f"Configured path ({path}) does not exist!")
            return

        self.worker = CollectWorker(self._name, str(path), self.config)
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)

        self.log_output.emit("Running pytest to collect available tests.")
        QtCore.QThreadPool.globalInstance().start(self.worker)

    def callback(self, name, rc, stdout, stderr, time):
        # XXX needed?
        self.run_results.emit(name, rc, stdout, stderr, time)
        if rc == 0:
            self.succeed("Finished!", [])
        else:
            self.fail("Internal failure, please check command outputs!")


class CollectWorker(Worker):
    test_info_re = re.compile("(\S+)::(\w+)(?:\[(\S+)\])?")

    def fn(self, working_dir: str, config):
        args = [
            "pytest",
            "--co",
            "-p", "no:terminalreporter",
            "-p", "no:sugar",
            "--hdl-verifgui"
        ]
        process = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE, cwd=working_dir)

        # { module: { test: CollectedTest } }
        tests: Dict[str, Dict[str, CollectedTest]] = {}

        for line in process.stdout.splitlines():
            line = line.decode('utf-8').strip()
            self.log_stdout(line)
            _info = line.split(",")

            if _info[0] != "COLLECT":
                continue

            info = self.test_info_re.match(_info[1])
            if not info:
                raise Exception("Unable to parse test!")

            module = info.group(1)
            test = info.group(2)
            coverage = True if _info[2].lower() == "true" else False
            regression = True if _info[2].lower() == "true" else False

            if module not in tests:
                tests[module] = {}
            if test not in tests[module]:
                tests[module][test] = CollectedTest(test, [], coverage, regression)

            # Test is parameterized, we need to collect the set of parameters to iterate through them.
            # TODO this might not really be necessary, there might be hooks I can latch onto earlier in
            # the collection process that give me the information without having to extract it like this.
            if info.group(3) is not None:
                _params = info.group(3).split("-")

                if len(tests[module][test].parameters) == 0:
                    tests[module][test].parameters = [set() for _ in _params]

                for i, param in enumerate(_params):
                    tests[module][test].parameters[i].add(param)

        # Sort parameters
        for module in tests:
            for test in tests[module]:
                tests[module][test].parameters = [list(s) for s in tests[module][test].parameters]
                for param in tests[module][test].parameters:
                    param.sort()

        with open(str(config.core_dir_path / "cocotb_tests.yaml"), "w") as f:
            f.write(dump(tests))

        return (0, "Test collection finished.", process.stderr.decode())

