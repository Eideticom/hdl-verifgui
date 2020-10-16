###############################################################################
## File: tasks/__init__.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################

from .base import Task, task_names, TaskFinishedDialog
from .parse import ParseTask
from .lint import LintTask
from .report import ReportTask
