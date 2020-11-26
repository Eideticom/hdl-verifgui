###############################################################################
# @file pyVerifGUI/tasks/base.py
# @package pyVerifGUI.tasks.base
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Base classes and utilities for creating a task
##############################################################################

from qtpy import QtCore, QtWidgets
from collections import namedtuple
from types import SimpleNamespace
from typing import List
import time

# Collection of names of tasks
# here to avoid some dependancy issues
task_names = SimpleNamespace()
task_names.parse = "Parser"
task_names.lint = "Linter"
task_names.report = "Report"


def is_task(cls):
    """Decorator to explicitly classify an object as a task.

    Using this vs just checking if the task inherits from Task allows you to
    build base tasks for common functionality. Also allows you to auto-import
    without pulling in the base task.
    """
    cls._is_task = True
    return cls


class Task(QtCore.QObject):
    """Base class to define a task that can be ran, but has other (Task) dependancies"""

    run_results = QtCore.Signal(str, int, str, str, float)
    run_stdout = QtCore.Signal(str, str)
    log_output = QtCore.Signal(str)

    # Returns a list of Tasks to be run. 0-lenth list =  no tasks to be run.
    # Status should be polled via finished(), not this signal
    task_result = QtCore.Signal(list)

    def __init__(self, config):
        """Do not override __init__! Instead define _post_init"""
        super().__init__()
        self.config = config

        # Default to not throwing any dialog
        self.throw_dialog = False
        self._running = False

        # Complete any task-specific init
        self._post_init()

    @property
    def _status(self) -> str:
        """Returns either "passed" or "failed" """
        try:
            return self.config.status[f"{self._name}"]["status"]
        except KeyError:
            return "failed"

    @_status.setter
    def _status(self, status: str):
        """Updates status"""
        # TODO come up with a way to migrate the two fields into one, that can transition nicely
        self.config.status.update({f"{self._name}": {
            "finished": self._finished,
            "status": status,
            "time": time.time(),
        }})

    @property
    def _finished(self) -> bool:
        """Returns whether Task has finished or not"""
        try:
            return self.config.status[self._name]["finished"]
        except KeyError:
            return False

    @_finished.setter
    def _finished(self, status):
        """Setter for finished status"""
        self.config.status.update({self._name: {
            "finished": status,
            "status": self._status,
            "time": time.time(),
        }})

    def reset(self):
        """Resets state of task. Overrule for more complex behaviour"""
        self.finished = False

    def kill(self):
        """Default safe implementation of kill"""
        worker = getattr(self, "worker", None)
        if worker is not None:
            worker.kill(True)

    #### ------
    # Required implementations
    def run(self, is_last=True):
        """Begins running the task.

        This should set running and finished appropriately during the task.
        Ideally set up some sort of asynchronous operation which uses
        callbacks and the such (signals and slots do nicely) to set state,
        especially if it is a long-running task.

        is_last: whether this Task is the end of a chain,
                 i.e. do we prompt for tasks to run afterwards?
        """
        raise NotImplementedError

    ## The below properties can simply be defined as class members.
    @property
    @classmethod
    def _deps(self) -> List[str]:
        """List of tasks required to have succeeded before this task can run

        Must be class method because it is used prior to instantiation"""
        raise NotImplementedError

    @property
    def _name(self) -> str:
        """Name to present"""
        raise NotImplementedError

    @property
    def _description(self) -> str:
        """Basic description of the task"""
        raise NotImplementedError

    #### ------
    # Optional Implementations

    def _post_init(self):
        """Task-specific initialization"""


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
