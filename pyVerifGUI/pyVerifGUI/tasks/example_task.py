from qtpy import QtCore
import time

from pyVerifGUI.tasks.base import Task, is_task
from pyVerifGUI.tasks.worker import Worker

#@is_task
class MyTask(Task):
    _deps = []
    _name = "my_task"
    _description = "My Cool Task"

    def _run(self):
        self.log_output.emit("Hello look this is my cool task that can do cool things.")
        self.log_output.emit("Starting task...")

        # Doing my super time-consuming task now...
        # GUI will be unresponsive if you don't at least throw this into a
        # QThreadPool or some other form of parallelism.
        # XXX there could likely be helper functions here to reduce the effort
        #     of doing something like this.
        self.worker = MyWorker(self._name, self.config)
        self.worker.signals.result.connect(self.callback)
        self.worker.signals.stdout.connect(self.run_stdout)

        QtCore.QThreadPool.globalInstance().start(self.worker)

    def callback(self, name, rc, stdout, stderr, time):
        self.log_output.emit(f"Finished my task in {time} seconds.")
        self.succeed("Finished!", [])

class MyWorker(Worker):
    def fn(self, stdout, config):
        self.signals.stdout.emit(self.tag, "Starting my time-consuming task!")
        time.sleep(5)
        self.signals.stdout.emit(self.tag, "Done my time-consuming task!")

        return (0, "", "")
