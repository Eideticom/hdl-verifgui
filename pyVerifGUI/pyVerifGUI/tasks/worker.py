###############################################################################
# @file pyVerifGUI/tasks/worker.py
# @package pyVerifGUI.tasks.worker
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Worker class to run tasks inside of a QThreadPool
##############################################################################

from qtpy import QtCore
from timeit import default_timer as timer
from collections import namedtuple
from types import SimpleNamespace
import traceback


class WorkerSignals(QtCore.QObject):
    """Worker completion signals"""
    finished = QtCore.Signal()
    # Runner ID, rc, stdout, stderr, time elapsed
    result = QtCore.Signal(str, int, str, str, float)
    # tag, text
    stdout = QtCore.Signal(str, str)
    stderr = QtCore.Signal(str, str)

    # Testing-specific signals
    # XXX I don't like this, not sure how I could make a more generic implementation
    run_began = QtCore.Signal(str, int)
    test_finished = QtCore.Signal()
    testing_complete = QtCore.Signal()


class Worker(QtCore.QRunnable):
    """By subclassing QRunnable we can pass this class to QThreadPool.start()"""

    # TODO find a nicer way than args and kwargs to pass things to the internal function
    def __init__(self, tag: str, *args, **kwargs):
        super().__init__()
        self.tag = tag
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.popen = None

    def run(self):
        """Implemented to execute passed function in a QThreadPool, with the given args

        The arguments to this function need to be passed in the constructor as well
        """

        # This implementation also times completion of the runner function
        start = timer()
        try:
            # TODO I should do a bit more error handling here and checking of arguments,
            # error messages can be a bit cryptic if you don't already know how this works
            returncode, stdout, stderr = self.fn(*self.args, **self.kwargs)
        except Exception as exc:
            stderr = '\n'.join(traceback.format_tb(exc.__traceback__))
            stderr += traceback.format_exc()
            returncode, stdout = (-42, "")
        finally:
            end = timer()

        # Emit signals
        # TODO error handling
        self.signals.result.emit(self.tag, returncode, stdout, stderr,
                                 end - start)
        self.signals.finished.emit()

    def fn(self, stdout, *args, **kwargs):
        """Override this for the subclass implementation!"""
        raise NotImplementedError

    # XXX it may make sense to move this to a seperate channel so it can
    # be specially redirected.
    def display_cmd(self):
        """Prints correctly formatted list of commands to stdout.

        Does nothing if self.cmd_list is not defined
        """
        if hasattr(self, 'cmd_list'):
            self.signals.stdout.emit(self.tag, f"**** {' '.join(self.cmd_list)}")

    def emit_stdout(self, label: str):
        """Prints popen output to stdout signal"""
        out = ""
        for line in self.popen.stdout:
            line = line.decode()
            self.signals.stdout.emit(label, line)
            out += line

        return self.popen.wait(), out

    def log_stdout(self, text: str):
        self.signals.stdout.emit(self.tag, text)

    def kill(self, really: bool):
        """Slot to kill worker"""
        # Some workers cannot be killed, and that is okay,
        # because they are quick anyways
        if self.popen is not None and really is True:
            self.popen.kill()
