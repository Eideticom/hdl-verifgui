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
from pyVerifGUI.gui.config import Config

from .base import Task, is_task, task_names
from .worker import Worker
from .parse import get_extra_args


@is_task
class LintTask(Task):
    _deps = [task_names.parse]
    _name = task_names.lint
    _description = "SystemVerilog Linter (Verilator)"

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

class LinterWorker(Worker):
    def fn(self, stdout, config: Config):
        """Run verilator as a linter and save the parsed output into the build
        directory.
        """
        del stdout

        if os.name == 'nt':
            verilator_exe = "verilator.exe"
        else:
            verilator_exe = "verilator"

        self.cmd_list = [verilator_exe, "--lint-only", "-Wall", "--top-module",
                         config.top_module, "-f", f"{config.build_path.resolve()}/rtlfiles.lst"]

        opts = config.config.get("verilator_args", None)
        self.cmd_list.extend(get_extra_args(opts))
        self.display_cmd()

        # can only be run after parsing has finished
        try:
            self.popen = sp.Popen(self.cmd_list,
                                  stdout=sp.PIPE,
                                  stderr=sp.PIPE,
                                  cwd=config.working_dir_path)
        except Exception as exc:
            return (-42, "", str(exc))

        stdout, stderr = self.popen.communicate()
        stderr = stderr.decode()
        returncode = self.popen.wait()
        message_text = stderr

        # Parse verilator output to build list of messages
        messages, errors = parse_verilator_output(message_text)
        if messages is None:
            return (-42, "", message_text)

        # Write messages to YAML storage file
        messages_path = config.build_path / "linter_messages.yaml"
        dump(messages, open(messages_path, "w"))

        errors_path = config.build_path / "linter_errors.yaml"
        if errors:
            dump(errors, open(errors_path, "w"))
        else:
            if errors_path.exists():
                os.remove(str(errors_path))

        return (returncode, stdout.decode(), stderr)