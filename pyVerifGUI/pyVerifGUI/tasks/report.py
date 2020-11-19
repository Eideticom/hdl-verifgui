###############################################################################
# @file pyVerifGUI/tasks/report.py
# @package pyVerifGUI.tasks.report
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Report generation task
##############################################################################

from typing import Callable

from .base import Task, task_names
from pyVerifGUI.gui.base_tab import Tab


class ReportTask(Task):
    _deps = [task_names.lint]
    _running = False
    _name = task_names.report
    _description = "Generate project report"

    _summary_fns = []
    _tabs = []

    def addSummaryFn(self, fn: Callable):
        """Append a summary function to the list of functions to run"""
        self._summary_fns.append(fn)

    def addTabSummary(self, tab: Tab):
        """Append a tab to the list of tabs to generate the report from"""
        self._tabs.append(tab)

    def run(self, is_last=True):
        """Generates a report"""
        text = f"""# Auto-Generated Verification Report for {self.config["repo_name"]}

- Top-level module: {self.config.top_module}
- Build: {self.config.build}

"""

        for tab in self._tabs:
            text += f"# {tab._display} Report\n\n"
            text += tab._report()
            text += "\n\n"

        for fn in self._summary_fns:
            text += fn()

        report = str((self.config.build_path / "final_report.md").resolve())
        self.log_output.emit(f"Writing final report to: {report}")

        with open(report, "w") as f:
            f.write(text)

        self.finished = True
        self.status = "passed"
        self.config.dump_build()
