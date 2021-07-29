###############################################################################
# @file pyVerifGUI/gui/models/message.py
# @package pyVerifGUI.gui.models.message
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Base class for generic message types.
##############################################################################

from qtpy import QtCore, QtGui
import os
from typing import Sequence, Union

from pyVerifGUI.gui.models import MessageType, MessageListType


class Messages:
    """Base class to contain lists of messages"""
    def __init__(self, messages: MessageListType, headers: MessageListType,
                 accessors: Sequence[str]):
        self.messages = messages
        self.headers = headers
        self.accessors = accessors

    def __len__(self):
        return len(self.messages)

    def __getitem__(self, position: int):
        return self.messages[position]

    def append(self, item: MessageType):
        self.messages.append(item)

    def remove(self, item: MessageType):
        self.messages.remove(item)


class AbstractMessageModel(QtCore.QAbstractItemModel):
    """Base model to represent a message to be displayed in a table"""
    def __init__(self, messages: MessageListType, waivers: MessageListType,
                 messageType: Messages, waiverType: Messages):
        super().__init__()
        # These are here so we can provide a more generic interface
        # Can easily be provided in the subclass's constructor
        self.messageType = messageType
        self.waiverType = waiverType

        # We maintain lists of messages so we can easily build new ones,
        # and don't have to juggle data around
        self.all_messages = messageType(messages)
        self.waivers = waiverType(waivers)
        self.unwaived_messages = None
        self.waived_messages = None
        self.orphans = None

        # These determine what messages are displayed to the user
        self.messages = self.all_messages
        self.selection = "all"

        self.view_full_filenames = False

        self.filterMessages()
        self.called = 0

    def isMessageEqual(self, a, b):
        """Required implementation of whether two messages are equal"""
        if a["file"] == b["file"] and a["lineno"] == b["lineno"]:
            if a["text_hash"] == b["text_hash"]:
                return True

        return False

    def filterMessages(self):
        """Builds list of waived and unwaived messages."""
        unwaived = []
        waived = []
        orphans = []

        # Build filtered lists
        for message in self.all_messages:
            is_waived = False

            # Check if message is waived
            for waiver in self.waivers:
                if self.isMessageEqual(message, waiver):
                    is_waived = True
                    break

            if is_waived:
                waived.append(message)
            else:
                unwaived.append(message)

        # Find orphaned waivers
        for waiver in self.waivers:
            is_orphan = True
            for message in waived:
                if self.isMessageEqual(message, waiver):
                    is_orphan = False
                    break

            if is_orphan:
                orphans.append(waiver)

        self.unwaived_messages = self.messageType(unwaived)
        self.waived_messages = self.messageType(waived)
        self.orphans = self.waiverType(orphans)
        # Update selection
        self.selectMessages(self.selection)

    def addWaiver(self, waiver: MessageType, rebuild=True):
        """Adds a waiver to the list of waivers"""
        self.waivers.append(waiver)
        if rebuild:
            self.filterMessages()

    def removeWaiver(self, waiver: MessageType, rebuild=True):
        """Removes an existing waiver from the list"""
        self.waivers.remove(waiver)
        if rebuild:
            self.filterMessages()

    def updateWaiver(self, old: MessageType, new: MessageType):
        """Replaces an existing waiver with a new waiver"""
        self.removeWaiver(old, rebuild=False)
        self.addWaiver(new)

    def findWaiver(self, message: MessageType) -> MessageType:
        """Finds the waiver associated with a given message"""
        for waiver in self.waivers:
            if self.isMessageEqual(waiver, message):
                return waiver

        return None

    def selectMessages(self, selection: str):
        """Change the type of messages to be displayed"""
        self.beginResetModel()
        self.selection = selection
        if selection == "all":
            self.messages = self.all_messages
        elif selection == "unwaived":
            self.messages = self.unwaived_messages
        elif selection == "waived":
            self.messages = self.waived_messages
        elif selection == "waivers":
            self.messages = self.waivers
        elif selection == "orphans":
            self.messages = self.orphans
        else:
            raise KeyError
        self.endResetModel()

    def index(self, row: int, column: int,
              parent: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """Returns the index of a requested item"""
        del parent
        if column < len(self.messages.headers):
            if row < len(self.messages):
                return self.createIndex(row, column, self.messages[row])

        return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """Parent in this case is always invalid"""
        del index
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        """Returns number of rows.

        Note: documentation states this must return 0 for a valid parent
        when used in a table-based model
        """
        if parent.isValid():
            return 0
        else:
            return len(self.messages)

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        """Returns the width of the displayed data"""
        del parent
        return len(self.messages.headers)

    def data(self, index: QtCore.QModelIndex,
             role: int) -> Union[str, QtGui.QColor]:
        """Returns the data associated with an index"""
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                if index.column() == 0:
                    return index.row()

                accessor = self.messages.accessors[index.column() - 1]
                data = self.messages[index.row()][accessor]
                if accessor == "file":
                    if not self.view_full_filenames:
                        return os.path.basename(data)
                return data
            elif role == QtCore.Qt.BackgroundColorRole:
                return self.getBackgroundColour(index)

    def getBackgroundColour(self, index: QtCore.QModelIndex) -> QtGui.QColor:
        """Returns the background colour for a given index"""
        message = self.messages[index.row()]
        #if self.findWaiver(message):
        if message.get("error", False):
            return QtGui.QColor(0xD0, 0, 0)
        elif self.findWaiver(message) is not None:
            return QtGui.QColor(0x60, 0x60, 0x60, 200)
        elif not message["waiver"]:
            if message["reviewed"]:
                return QtGui.QColor(0xFF, 169, 0)
            if message["unimplemented"]:
                return QtGui.QColor(0xD0, 0x20, 0, 200)

        return QtGui.QColor(0xE0, 0xD0, 0, 200)

    def headerData(self, column: int, orientation: int, role: int) -> str:
        """Returns the appropriate data for the headers"""
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if column == 0:
                return None
            return self.messages.headers[column - 1]


class AbstractDiffMessageModel(AbstractMessageModel):
    """Subclass to handle the diff of messages/waivers

    Subclass in order to avoid re-writing some of the Model logic
    """
    def __init__(self, current_messages: MessageListType,
                 compare_messages: MessageListType,
                 current_waivers: MessageListType,
                 compare_waivers: MessageListType, messageType: Messages,
                 waiverType: Messages):
        # Storage so we can update without rebuilding the model
        self.current_messages = current_messages
        self.compare_messages = compare_messages
        self.current_waivers = current_waivers
        self.compare_waivers = compare_waivers

        super().__init__(current_messages, current_waivers, messageType,
                         waiverType)

    def filterMessages(self):
        """Builds the differential lists of messages and waivers"""
        messages = self.generateDiffs(self.current_messages,
                                      self.compare_messages)
        waivers = self.generateDiffs(self.current_waivers,
                                     self.compare_waivers)

        self.all_messages = self.messageType(messages)
        self.waivers = self.waiverType(waivers)

        super().filterMessages()

    def generateDiffs(self, current: MessageListType,
                      compare: MessageListType) -> MessageListType:
        """Adds differential dicts from current and compare to storage"""
        storage = []
        for message in current:
            if message not in compare:
                message.update({"diffType": "add"})
                storage.append(message)
        for message in compare:
            if message not in current:
                message.update({"diffType": "remove"})
                storage.append(message)
        return storage

    def getBackgroundColour(self, index: QtCore.QModelIndex) -> QtGui.QColor:
        """Returns the background colour for a given index"""
        if index.internalPointer()["diffType"] == "add":
            colour = QtGui.QColor(0x00, 0xD0, 0x00)
        else:
            colour = QtGui.QColor(0xD0, 0x00, 0x00)

        return colour
