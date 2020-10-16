###############################################################################
## File: gui/models/lint.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Class definitions for linter messages"""

from qtpy import QtCore, QtGui

from pyVerifGUI.gui.models import MessageListType

from .message import AbstractMessageModel, AbstractDiffMessageModel, Messages


class LintMessages(Messages):
    """Describes linter messages"""
    def __init__(self, messages: MessageListType):
        self.messages = messages
        self.headers = ["File", "Line", "Column", "Type", "Information"]
        self.accessors = ["file", "row", "column", "type", "text"]


class LintWaivers(Messages):
    """Describes linter waivers"""
    def __init__(self, waivers: MessageListType):
        self.messages = waivers
        self.headers = [
            "File", "Line", "Type", "Author", "Date", "Reason", "Context"
        ]
        self.accessors = [
            "file", "row", "type", "author", "date", "reason", "text"
        ]


class LintMessageModel(AbstractMessageModel):
    """Abstract model class to represent a linter message"""
    def __init__(self, messages: MessageListType, waivers: MessageListType):
        """Messages come directly from parsed linter_messages.yaml"""
        super().__init__(messages, waivers, LintMessages, LintWaivers)


class DiffLintMessageModel(AbstractDiffMessageModel):
    """Subclass to handle the diff of messages/waivers

    Subclass in order to avoid re-writing some of the Model logic
    """
    def __init__(self, current_messages: MessageListType,
                 compare_messages: MessageListType,
                 current_waivers: MessageListType,
                 compare_waivers: MessageListType):
        super().__init__(current_messages, compare_messages, current_waivers,
                         compare_waivers, LintMessages, LintWaivers)
