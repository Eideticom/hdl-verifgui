###############################################################################
# @file pyVerifGUI/gui/models/design.py
# @package pyVerifGUI.gui.models.design
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Models used in the Design tab
##############################################################################

# Required to use type annotations that describe the current type
from __future__ import annotations

import qtpy
from qtpy.QtCore import QAbstractItemModel, QModelIndex
from typing import Mapping, Sequence

from pyVerifGUI.gui.models import MessageType


class ModuleTreeItem:
    """Item to represent each module in the design module hierarchy"""
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.index = None

    def appendChild(self, child: ModuleTreeItem):
        """Adds a child module"""
        self.children.append(child)

    def child(self, row: int) -> ModuleTreeItem:
        """Returns the specified child"""
        if row < 0 or row >= len(self.children):
            return None
        return self.children[row]

    def childCount(self) -> int:
        """Counts the number of sub-modules"""
        return len(self.children)

    def row(self) -> int:
        """Returns the index of this child to it's parent"""
        if self.parent is not None:
            for i, child in enumerate(self.parent.children):
                if child == self:
                    return i

        return 0

    def data(self) -> str:
        """Accessor for module name"""
        return self.name

    def parentItem(self) -> ModuleTreeItem:
        """Returns the parent"""
        return self.parent

    def build(self, in_tree: Mapping[str, Sequence[Mapping]]):
        """Builds a full tree, with self as the root node from a dictionary tree"""
        for key in in_tree.keys():
            child = ModuleTreeItem(key, self)
            self.appendChild(child)
            child.build(in_tree[key])


class ModuleTreeItemModel(QAbstractItemModel):
    """Implements the functions require to implement the model class for use
    in a QTreeView instance
    """
    def __init__(self, tree: ModuleTreeItem):
        super().__init__()
        self.tree_root = tree

    def index(self, row: int, column: int, parent: QModelIndex) -> QModelIndex:
        """Required subclass implementation. Returns the lookup index of the requested
        item
        """
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.tree_root
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item is not None:
            return self.createIndex(row, column, child_item)

        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Required subclass implementation. Returns the lookup index of the given item's parent"""
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parentItem()

        if parent_item == self.tree_root:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QModelIndex) -> int:
        """Required subclass implementation. Returns the number of the item's children"""
        if not parent.isValid():
            parent_item = self.tree_root
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent: QModelIndex) -> int:
        """Required subclass implementation. Must return 1 for use in QTreeView"""
        del parent
        return 1

    def data(self, index: QModelIndex, role: int) -> str:
        """Required subclass implementation. Returns the associated data for the View

        In this case, we only need to return the name of the module
        """
        if role == qtpy.QtCore.Qt.DisplayRole:
            return index.internalPointer().data()

        return None

    def headerData(self, column: int, orientation: qtpy.QtCore.Qt.Orientation,
                   role: int) -> str:
        """Required subclass implementation. We only want one header, as a title"""
        del column, orientation
        if role == qtpy.QtCore.Qt.DisplayRole:
            return "Design Module Hierarchy"

        return None
