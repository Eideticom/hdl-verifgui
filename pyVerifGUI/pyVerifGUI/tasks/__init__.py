###############################################################################
# @file pyVerifGUI/tasks/__init__.py
# @package pyVerifGUI.tasks
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Tasks that the GUI can run
##############################################################################

from .base import Task, task_names, TaskFinishedDialog
from .parse import ParseTask
from .lint import LintTask
from .report import ReportTask
