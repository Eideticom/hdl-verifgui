###############################################################################
# @file pyVerifGUI/gui/tabs/runnerwidget.py
# @package pyVerifGUI.gui.tabs.runnerwidget
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Sub-widget for overview than handles running tasks
##############################################################################
from importlib import import_module
from qtpy import QtCore, QtWidgets
from collections import namedtuple, deque
from functools import partial
from pathlib import Path
from typing import List
import inspect
import os

from pyVerifGUI.tasks.base import (Task, TaskFailedDialog,
                              TaskFinishedDialog, task_names)
from pyVerifGUI.plugin_utils import import_plugins
import pyVerifGUI.tasks

class InvalidTaskError(Exception):
    """Exception raised when a task is not added to the list of tasks"""
    def __init__(self, task_name):
        self.message = f"{task_name} not a valid task. Couldn't be found in the task list!"


class TaskFailedError(Exception):
    """Raised when a dependancy is failed"""
    def __init__(self, task_name):
        self.task = task_name
        self.message = f"{task_name} failed!"


class Runner(QtWidgets.QWidget):

    run_results = QtCore.Signal(str, int, str, str, float)
    run_stdout = QtCore.Signal(str, str)
    log_output = QtCore.Signal(str)

    task_finished = QtCore.Signal()

    run_began = QtCore.Signal(str, int)
    test_finished = QtCore.Signal()
    testing_complete = QtCore.Signal()

    # "Internal" signal for killing tests
    kill_test = QtCore.Signal(str)

    def __init__(self, parent, config, task_folders: List):
        super().__init__(parent)

        self.config = config

        # Flag so changing thread counts above warn limit isn't so annoying
        self.thread_warned = False

        ## A bunch of widget BS goes here
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)

        # select max number of threads
        self.thread_label = QtWidgets.QLabel(self)
        self.thread_label.setText("Max Number of threads to use")
        self.thread_select = QtWidgets.QSpinBox(self)
        self.thread_select.setMinimum(1)
        self.thread_select.setMaximum(os.cpu_count() * 2)
        self.thread_select.setValue(os.cpu_count() / 2)
        self.thread_select.valueChanged.connect(self.checkThreadsValue)

        self.layout.addWidget(self.thread_label, 0, 0)
        self.layout.addWidget(self.thread_select, 0, 2)

        self.TaskInfo = namedtuple('TaskInfo', ['task', 'label', 'button'])
        self.tasks = []
        self.compilation_tasks = []
        self.run_list = deque([])
        self.task_is_running = False  # needed to not launch extra tasks when something is running

        used_tasks = []
        plugin_dirs = [Path(inspect.getfile(pyVerifGUI.tasks)).resolve().parent]
        plugin_dirs.extend([Path(path) for path in task_folders])
        self.task_plugins = import_plugins(plugin_dirs, lambda obj: getattr(obj, "_is_task", False))
        for task in self.task_plugins:
            if task not in used_tasks:
                new_tasks = self.taskSort(task)
                used_tasks.extend([task for task in new_tasks if task not in used_tasks])

        # Sort tasks by dependancies
        for task in used_tasks:
            self.addTask(task)

        # Little dialog to open if we haven't done anything in a build yet
        self.new_build_dialog = TaskFinishedDialog("New Build Opening")
        self.new_build_dialog.addNextTask(task_names.parse)
        self.new_build_dialog.addNextTask(task_names.lint)

    def taskSort(self, task):
        """Sorts task by dependancies"""
        tasks = []
        for dep in task._deps:
            dep = next((task for task in self.task_plugins if task._name == dep))
            tasks.append(dep)

        tasks.append(task)

        return tasks

    def killAllTasks(self):
        """Kills all running tasks"""
        for task in self.tasks:
            if task.task._running:
                try:
                    task.task.kill()
                except:
                    pass

    def checkThreadsValue(self, threads: int):
        """Pops a warning box if selected number of threads exceeds cores"""
        if threads > os.cpu_count():
            if not self.thread_warned:
                delta = threads - os.cpu_count()
                text = f"You have selected to run {threads} threads, which exceeds your core count ({os.cpu_count()}) by {delta}. "
                text += "This may cause your system to become unresponsive."
                QtWidgets.QMessageBox.information(
                    self, "Threads selected exceed physical cores", text)
                self.thread_warned = True
        else:
            self.thread_warned = False

    def addTask(self, task: Task):
        """Adds a task, along with associated buttons and signals to widget"""
        # Instantiate
        task = task(self.config)

        # Create widgets
        row = self.layout.rowCount()
        label = QtWidgets.QLabel(task._description, self)
        button = QtWidgets.QPushButton(task._name, self)
        button.setEnabled(False)

        # Add to list of tasks
        self.tasks.append(self.TaskInfo(task, label, button))

        # Add to layout
        self.layout.addWidget(label, row, 0)
        self.layout.addWidget(button, row, 1)

        # Manage signals
        task.run_results.connect(self.run_results)
        task.run_stdout.connect(self.run_stdout.emit)
        task.log_output.connect(self.log_output)
        task.task_result.connect(self.handleTaskCompletion)

        # I *knew* I missed some coverage code
        # Not all tasks have these signals
        try:
            task.run_began.connect(self.run_began)
            task.test_finished.connect(self.test_finished)
            task.testing_complete.connect(self.testing_complete)
            self.kill_test.connect(task.killTest)
        except AttributeError:
            pass

        # Only compilation tasks have these signals
        try:
            task.reset_compilation.connect(self.resetCompilation)
            self.compilation_tasks.append(task)
        except AttributeError:
            pass

        # Ensure task exists in status
        if not self.config.status.get(task._name):
            self.config.status.update({
                task._name: {
                    "finished": False,
                }
            })

        button.clicked.connect(partial(self.handleButtonPress, task))

    def handleButtonPress(self, task: Task):
        """Handles pressing the "management" button. Starts, kills or resets the task"""
        if task._finished:
            task.reset()
        elif task._running:
            try:
                task.kill()
                self.log_output.emit(f"Task {task._name} killed.")
            except AttributeError:
                self.log_output.emit(f"Task {task._name} could not be killed!")
        else:
            self.startTask(task)

        self.updateButtons()

    def resetCompilation(self):
        """Resets compilation status"""
        self.log_output.emit("Resetting old compilations.")
        for task in self.compilation_tasks:
            task._finished = False

        self.config.dump_build()

    def prepareTask(self, task: Task):
        """Adds task's required tasks to run list, as well as the task"""
        for req in task._deps:
            req_task = self.getTask(req)
            if req_task is None:
                raise InvalidTaskError(req)

            if not req_task._finished:
                # Adds ALL dependancies to run list
                self.prepareTask(req_task)

            if req_task._status == "killed" or req_task._status == "failed":
                raise TaskFailedError(req_task._name)

        # add task to list
        self.run_list.append(task._name)

    def startTask(self, task: Task):
        """Handles button press, starts the task running"""
        try:
            self.prepareTask(task)
            self.runNextTask()
        except TaskFailedError as exc:
            QtWidgets.QMessageBox.information(self, "Dependancy Failed!",
                                              f"{exc.task} failed, please correct issues and re-run.")

    def updateBuildStatus(self):
        """Updates state on a new build opening"""
        self.updateButtons()
        if self.config.new_build:
            # TODO find a better place for this config status dump
            for task in self.tasks:
                task.task._finished = False
            self.config.dump_build()
            tasks = self.new_build_dialog.run(
                "New task opened! Select the task you want to run until.")
            self.config.new_build = False

            for task_name in tasks:
                self.prepareTask(self.getTask(task_name))

            self.runNextTask()

    def updateButtons(self):
        """Updates button status"""
        for task in self.tasks:
            if self.config.build is None:
                # No build!
                task.button.setEnabled(False)
                task.button.setText("No Build Selected!")
                task.button.setStyleSheet("background-color: red")
            else:
                task.button.setEnabled(True)
                if task.task._finished:
                    if task.task._status == "passed":
                        task.button.setStyleSheet("background-color: green")
                        task.button.setText(f"Reset {task.task._name}")
                    else:
                        task.button.setStyleSheet("background-color: orange")
                        task.button.setText(f"{task.task._name} failed!")
                elif task.task._running:
                    task.button.setStyleSheet("background-color: red")
                    if hasattr(task.task, "kill"):
                        task.button.setText(f"Kill {task.task._name}")
                    else:
                        task.button.setEnabled(False)
                        task.button.setText(f"{task.task._name} Running...")
                else:
                    task.button.setStyleSheet("background-color: yellow")
                    task.button.setText(f"Run {task.task._name}")

    def getTask(self, task_name: str):
        """Gets the task object for the given task name"""
        for task in self.tasks:
            if task.task._name == task_name:
                return task.task

    def getBlocking(self, task: Task):
        """Returns blocking task, or None if not blocking"""
        for req in task._deps:
            if not self.getTask(req)._finished:
                return task._name

    def handleTaskCompletion(self, status: bool, task_name: str, msg: str, post_tasks: list):
        """Handles task completion, running the next task or showing
        completion dialog.
        """
        # Save status information
        self.config.dump_build()

        # Only throw dialogs if this is the last task
        if len(self.run_list) == 0:
            if status:
                dialog = TaskFinishedDialog(task_name)
                for task in post_tasks:
                    dialog.addNextTask(task)
                self.run_list.extend(dialog.run(msg))
            else:
                dialog = TaskFailedDialog(task_name)
                dialog.run(msg)

        self.runNextTask()
        self.task_finished.emit()


    def runNextTask(self):
        """Runs the next task in the queue"""
        # Launch next task in list if we have more to run
        if len(self.run_list) > 0:
            next_name = self.run_list.popleft()
            next_task = self.getTask(next_name)
            if next_task is None:
                raise InvalidTaskError(next_name)

            # Only run if it hasn't been run already
            if not next_task._finished and not next_task._running:
                next_task.run()
                self.task_is_running = True
            else:
                if not self.task_is_running:
                    self.runNextTask()

        self.updateButtons()
