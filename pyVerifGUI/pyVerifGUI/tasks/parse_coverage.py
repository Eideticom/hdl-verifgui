###############################################################################
# @file pyVerifGUI/tasks/parse_coverage.py
# @package pyVerifGUI.tasks.parse_coverage
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Task to parse verilator coverage files and generate the appropriate messages
##############################################################################
import hashlib
from oyaml import dump


from qtpy import QtCore


from pyVerifGUI.tasks.base import Task, is_task, task_names
from pyVerifGUI.tasks.worker import Worker
from pyVerifGUI.gui.config import Config


@is_task
class ParseCoverageTask(Task):
    _deps = [task_names.parse]
    _name = "parse_coverage"
    _description = "Parse output coverage files"

    def _run(self):
        self.worker = ParseCoverageWorker(self._name, self.config)
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)

        QtCore.QThreadPool.globalInstance().start(self.worker)


    def callback(self, name, rc, stdout, stderr, time):
        self.succeed("Finished!", [])


class ParseCoverageWorker(Worker):
    def fn(self, stdout, config: Config):
        """Runner to parse the coverage-annotated source files and build a list of issues"""
        messages = []
        covered = 0
        total = 0
        for f in (config.build_path / "coverage_files").resolve().iterdir():
            data = f.read_text()
            for row, line in enumerate(data.splitlines()):
                total += 1

                # lines beginning with % are lines with issues
                if line[0] == "%":
                    covered += 1
                    # Annotated lines with issues look like this:
                    # %xxxxxxxx\tsource_line_goes_here\n
                    # The tab seperates the count from the line contents
                    line = line.split("\t", 1)
                    messages.append({
                        "file":
                        str(f),
                        # the "row" here is 1-indexed because it translates to line number
                        "waiver":
                        False,
                        "row":
                        row + 1,
                        "text":
                        line[1],
                        "count":
                        int(line[0][1:]),
                        "text_hash":
                        int(
                            hashlib.md5(line[1].encode('utf-8')).hexdigest(),
                            16),
                        "comment":
                        "N/A",
                        "legitimate":
                        False,
                    })

        config.status["covered_count"] = covered
        config.status["coverage_count"] = total

        dump(messages,
             open(str(config.build_path / "coverage_messages.yaml"), "w"))

        return (0, "", "")
