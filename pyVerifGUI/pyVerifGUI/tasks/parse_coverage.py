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
from pathlib import Path
import hashlib


from qtpy import QtCore, QtWidgets
from oyaml import dump


from pyVerifGUI.tasks.base import Task, is_task, task_names
from pyVerifGUI.tasks.worker import Worker
from pyVerifGUI.gui.config import Config


@is_task
class ParseCoverageTask(Task):
    _deps = []
    _name = "parse_coverage"
    _description = "Parse output coverage files"

    def _run(self):
        cov_files: Path = (self.config.build_path / "coverage_files").resolve()
        if not cov_files.exists():
            if not LookForCoverageDialog().exec_():
                self.fail("No coverage files to parse!")

            folder = QtWidgets.QFileDialog.getExistingDirectory(
                None,
                "Open coverage files",
                str(self.config.core_dir_path)
            )
            if len(folder) > 0:
                cov_files = Path(folder)
            else:
                self.fail("No coverage files to parse!")


        self.worker = ParseCoverageWorker(self._name, self.config, cov_files)
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)

        QtCore.QThreadPool.globalInstance().start(self.worker)


    def callback(self, name, rc, stdout, stderr, time):
        self.succeed("Finished!", [])


class LookForCoverageDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()

        self.setLayout(QtWidgets.QVBoxLayout(self))

        self.info = QtWidgets.QLabel(
            "Unable to find appropriate coverage files in build directory. Do you want to open some manually?",
            self
        )

        self.buttons = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal)
        self.yes = QtWidgets.QPushButton("Yes")
        self.no = QtWidgets.QPushButton("No")
        self.buttons.addButton(self.yes, self.buttons.AcceptRole)
        self.buttons.addButton(self.no, self.buttons.RejectRole)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout().addWidget(self.info)
        self.layout().addWidget(self.buttons)


class ParseCoverageWorker(Worker):
    def fn(self, config: Config, cov_files_folder: Path):
        """Runner to parse the coverage-annotated source files and build a list of issues"""
        messages = []
        covered = 0
        total = 0

        for f in cov_files_folder.iterdir():
            data = f.read_text()
            for row, line in enumerate(data.splitlines()):
                total += 1

                if len(line) == 0:
                    continue

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
