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
        # TODO these connections should be consolidated
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.result.connect(self.run_results)
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
        uncovered = 0
        total = 0

        for f in cov_files_folder.iterdir():
            # Keeps track of the extra lines that verilator inserts and adjusts for them
            verilator_correction = 1 # 1 extra comment line at top

            if not f.is_file():
                continue

            data = f.read_text()
            for row, line in enumerate(data.splitlines()):
                if len(line) == 0:
                    continue

                verilator_cov_line = "verilator_coverage:" in line
                if verilator_cov_line:
                    verilator_correction += 2

                # lines beginning with % are lines with issues
                if line[0] == "%":
                    uncovered += 1
                    # Annotated lines with issues look like this:
                    # %xxxxxxxx\tsource_line_goes_here\n
                    # The tab seperates the count from the line contents
                    line = line.split("\t", 1)

                    # 1-indexed, so corrected relative to 0-indexing
                    if verilator_cov_line:
                        lineno = row
                    else:
                        lineno = row + 1 - verilator_correction

                    messages.append({
                        "file": str(f),
                        "waiver": False,
                        "lineno": lineno,
                        "cov_file_lineno": row + 1,
                        "text": line[1],
                        "count": int(line[0][1:]),
                        "text_hash": int(
                            hashlib.md5(line[1].encode('utf-8')).hexdigest(), 16
                        ),
                        "comment": "N/A",
                        "reviewed": False,
                        "unimplemented": False,
                    })

                if line[0] == "%" or line[0] == " ":
                    total += 1

        config.status["uncovered_count"] = uncovered
        config.status["coverage_total"] = total

        dump(messages,
             open(str(config.build_path / "coverage_messages.yaml"), "w"))

        return (0, "", "")
