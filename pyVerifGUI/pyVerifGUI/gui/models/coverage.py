"""Data models for coverage messages"""

__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from qtpy import QtCore, QtGui

from pyVerifGUI.gui.models import MessageListType, MessageType

from .message import AbstractMessageModel, AbstractDiffMessageModel, Messages


class CoverageMessages(Messages):
    """Defines coverage messages"""
    def __init__(self, messages: MessageListType):
        self.messages = messages
        self.headers = ["File", "Line", "Hits", "Context"]
        self.accessors = ["file", "lineno", "count", "text"]


class CoverageWaivers(Messages):
    """Defines coverage waivers"""
    def __init__(self, messages: MessageListType):
        self.messages = messages
        self.headers = [
            "File", "Line", "Date", "Author", "Reason", "Explanation",
            "Context"
        ]
        self.accessors = [
            "file", "lineno", "date", "author", "reason", "explanation", "text"
        ]


class CoverageMessageModel(AbstractMessageModel):
    """A message model for coverage messages for use in a QTableView"""
    def __init__(self, messages: MessageListType, waivers: MessageType):
        super().__init__(messages, waivers, CoverageMessages, CoverageWaivers)


class CoverageDiffMessageModel(AbstractDiffMessageModel):
    """A message model for viewing the difference between coverage messages

    For use in a QTableView
    """
    def __init__(self, current_messages: MessageListType,
                 compare_messages: MessageType,
                 current_waivers: MessageListType,
                 compare_waivers: MessageType):
        super().__init__(current_messages, compare_messages, current_waivers,
                         compare_waivers, CoverageMessages, CoverageWaivers)
