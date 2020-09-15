__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from typing import Callable

from .base import Task, task_names


class ReportTask(Task):
    _deps = [task_names.lint]
    _running = False
    _name = task_names.report
    _description = "Generate project report"

    _summary_fns = []

    def addSummaryFn(self, fn: Callable):
        """Append a summary function to the list of functions to run"""

        self._summary_fns.append(fn)

    def run(self, is_last=True):
        """Generates a report"""
        text = f"""# Auto-Generated Verification Report for {self.config["repo_name"]}

- Top-level module: {self.config.top_module}
- Build: {self.config.build}

"""

        for fn in self._summary_fns:
            text += fn()

        report = str((self.config.build_path / "final_report.md").resolve())
        self.log_output.emit(f"Writing final report to: {report}")

        with open(report, "w") as f:
            f.write(text)

        self.finished = True
        self.status = "passed"
        self.config.dump_build()