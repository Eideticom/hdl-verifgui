###############################################################################
## File: tasks/worker.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Worker class which enables running tasks inside of a QThreadPool"""

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
            returncode, stdout, stderr = self.fn(self.signals.stdout,
                                                 *self.args, **self.kwargs)
        except Exception as exc:
            stderr = '\n'.join(traceback.format_tb(exc.__traceback__))
            stderr += traceback.format_exc(exc)
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

    def kill(self, really: bool):
        """Slot to kill worker"""
        # Some workers cannot be killed, and that is okay,
        # because they are quick anyways
        if self.popen is not None and really is True:
            self.popen.kill()
