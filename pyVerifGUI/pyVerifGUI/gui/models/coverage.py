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
        self.accessors = ["file", "row", "count", "text"]


class CoverageWaivers(Messages):
    """Defines coverage waivers"""
    def __init__(self, messages: MessageListType):
        self.messages = messages
        self.headers = [
            "File", "Line", "Date", "Author", "Reason", "Explanation",
            "Context"
        ]
        self.accessors = [
            "file", "row", "date", "author", "reason", "explanation", "text"
        ]


class CoverageMessageModel(AbstractMessageModel):
    """A message model for coverage messages for use in a QTableView"""
    def __init__(self, messages: MessageListType, waivers: MessageType):
        super().__init__(messages, waivers, CoverageMessages, CoverageWaivers)

    def getBackgroundColour(self, index: QtCore.QModelIndex):
        """Overridden here to avoid KeyError"""
        message = index.internalPointer()
        if not message["waiver"]:
            if message["legitimate"]:
                return QtGui.QColor(0xFF, 0x45, 0)
        return QtGui.QColor(0xD4, 0xD2, 0x00)


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
