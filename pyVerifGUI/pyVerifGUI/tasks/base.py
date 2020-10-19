###############################################################################
## File: tasks/base.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################

from qtpy import QtCore, QtWidgets
from collections import namedtuple
from types import SimpleNamespace
from typing import List

# Collection of names of tasks
# here to avoid some dependancy issues
task_names = SimpleNamespace()
task_names.parse = "Parser"
task_names.lint = "Linter"
task_names.report = "Report"


class Task(QtCore.QObject):
    """Base class to define a task that can be ran, but has other (Task) dependancies"""

    run_results = QtCore.Signal(str, int, str, str, float)
    run_stdout = QtCore.Signal(str, str)
    log_output = QtCore.Signal(str)

    # Returns a list of Tasks to be run. 0-lenth list =  no tasks to be run.
    # Status should be polled via finished(), not this signal
    task_result = QtCore.Signal(list)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.throw_dialog = False

    # I'm not sure if it's better to do this or to just use duck typing
    # On the one hand, this clearly defines what is required
    # on the other, this is quite a few extra lines to not really DO anything
    @property
    def requirements(self) -> List[str]:
        """Returns list of requirements to run() this task"""
        return self._deps

    @property
    def status(self) -> str:
        """Returns either "passed" or "failed" """
        return self.config.status.get(f"{self._name}_status", None)

    @status.setter
    def status(self, status: str):
        """Updates status"""
        # TODO come up with a way to migrate the two fields into one, that can transition nicely
        self.config.status.update({f"{self._name}_status": status})

    @property
    def finished(self) -> bool:
        """Returns whether Task has finished or not"""
        try:
            return self.config.status[self._name]
        except KeyError:
            return False

    @finished.setter
    def finished(self, status):
        """Setter for finished status"""
        self.config.status.update({self._name: status})

    @property
    def running(self) -> bool:
        """Returns if the task is currently running"""
        return self._running

    @property
    def name(self) -> str:
        """Human-readable name for Task"""
        return self._name

    @property
    def description(self) -> str:
        """Short-ish text about task"""
        return self._description

    def run(self, is_last=True):
        """Begins running the task

        is_last: whether this Task is the end of a chain,
                 i.e. do we prompt for tasks to run afterwards?
        """
        raise NotImplementedError

    def reset(self):
        """Resets state of task. Overrule for more complex behaviour"""
        self.finished = False

    def kill(self):
        """Default safe implementation of kill"""
        worker = getattr(self, "worker", None)
        if worker is not None:
            worker.kill(True)


class TaskFinishedDialog(QtWidgets.QDialog):
    """Template for a common dialog to popup on task completion"""

    rerun_task = QtCore.Signal()

    def __init__(self, task_name: str):
        super().__init__()
        self.setModal(True)

        self.setWindowTitle(f"{task_name} Completion")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.msg = QtWidgets.QLabel(self)
        self.button_box = QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal,
                                                     self)
        self.button_box.addButton(self.button_box.Ok)
        self.rerun_button = QtWidgets.QPushButton(f"Re-run {task_name}", self)
        self.rerun_button.clicked.connect(self.rerun)
        self.button_box.addButton(self.rerun_button,
                                  self.button_box.RejectRole)

        self.layout.addWidget(self.msg)
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)

        # List of buttons to check
        self.TaskButton = namedtuple('TaskButton', ['button', 'task'])
        self.next_tasks = []

    def rerun(self):
        """Slot to handle rerunning task"""
        self.reject()
        self.rerun_task.emit()

    def run(self, message: str) -> List[str]:
        """Open the dialog"""
        self.msg.setText(message)

        task_list = []
        if self.exec_():
            # Ok, so add any selected tasks to list
            for task_button in self.next_tasks:
                if task_button.button.isChecked():
                    task_list.append(task_button.task)

        return task_list

    def addNextTask(self, task_name: str):
        """Adds a task that can be run after this task"""
        button = QtWidgets.QRadioButton(f"Run {task_name}", self)
        self.next_tasks.append(self.TaskButton(button, task_name))
        self.button_box.addButton(button, self.button_box.NoRole)


class TaskFailedDialog(QtWidgets.QDialog):
    """Common popup for task (or subtask) failure"""
    def __init__(self, task_name: str, message: str):
        super().__init__()
        self.setModal(True)

        self.setWindowTitle(f"{task_name} Failed!")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.msg = QtWidgets.QLabel(self)
        self.msg.setText(message)
        self.button_box = QtWidgets.QDialogButtonBox(self)
        self.button_box.addButton(self.button_box.Ok)
        self.layout.addWidget(self.msg)
        self.layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
