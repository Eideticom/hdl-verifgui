###############################################################################
## File: gui/editor/editor.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Class definitions to implement a very basic editor

Supports opening and saving multiple files, in tabs.
"""

from qtpy import QtWidgets, QtGui, QtCore
import os

from .highlighting import SVHighlighter, YAMLHighlighter


class Editor(QtWidgets.QWidget):
    """Widget for editer. Meant to be implemented as a tab under a QTabWidget"""
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.old_filename = ""

        self.layout = QtWidgets.QVBoxLayout(self)

        self.tab_widget = QtWidgets.QTabWidget(self)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.closeTab)
        self.tabs = []

        self.layout.addWidget(self.tab_widget)

        # Optional view only tab
        self.view_only_tab = None

    def viewFile(self, filename: str, line_num: int = -1):
        """Opens the file for viewing in a permanent "viewing" tab"""
        if self.view_only_tab is None:
            self.tabs.insert(0, ViewFileTab(self))
            self.tab_widget.insertTab(0, self.tabs[0], "File Viewer")
            self.view_only_tab = True

        self.tabs[0].openFile(filename, line_num)

    def loadFile(self, filename: str, line_num: int = -1, always_new=True):
        """Opens a new editor tab with the given file.

        Places a marker at the given line_num, if specified.
        """
        # Don't open new file if one is loaded
        if not always_new:
            for tab in self.tabs:
                if tab.filename == filename:
                    return

        editor = EditorTab(self.tab_widget)
        editor.openFile(filename, line_num)
        self.tabs.append(editor)
        self.tab_widget.addTab(editor, filename)

        self.tab_widget.setCurrentIndex(len(self.tabs) - 1)
        self.tab_widget.tabBar().setCurrentIndex(len(self.tabs) - 1)

    def closeTab(self, index: int):
        """Attempts to close given tab

        Only fails to close the tab when the user selects Cancel on the popup save prompt
        """
        tab = self.tabs[index]
        self.tab_widget.setCurrentIndex(index)
        self.tab_widget.tabBar().setCurrentIndex(index)
        if tab.close():
            self.tab_widget.removeTab(index)
            self.tabs.remove(tab)
            return True

        return False


class FileTab(QtWidgets.QWidget):
    """Base-class for other types of tabs"""
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout)

        self.editor = CodeEditor(self)
        self.editor.cursorPositionChanged.connect(self.printPosition)
        font = QtGui.QFont("monospace")
        font.setPixelSize(12)
        self.editor.document().setDefaultFont(font)

        self.button_widget = QtWidgets.QWidget(self)
        self.button_layout = QtWidgets.QHBoxLayout(self.button_widget)
        self.position_text = QtWidgets.QLabel(self)
        self.file_text = QtWidgets.QLabel(self)
        self.file_text.setAlignment(QtCore.Qt.AlignCenter)
        self.button_layout.addWidget(self.position_text)
        self.button_layout.addWidget(self.file_text)
        self.button_layout.setStretch(1, 1)

        self.layout.addWidget(self.editor)
        self.layout.addWidget(self.button_widget)

        self.filename = ""
        self.file = None

    def openFile(self, filename: str, cursor_position: int = -1):
        """Opens a file and loads it into the editor"""
        if self.file:
            self.file.close()

        self.line = cursor_position

        self.filename = filename
        self.file = open(self.filename, "r+")
        self.editor.setPlainText(self.file.read())
        self.file_text.setText(filename)

        suffix = filename.split('.')[-1]
        if not hasattr(self, "highlighter"):
            if suffix == "sv" or suffix == "v":
                self.highlighter = SVHighlighter(self.editor.document())
            if suffix == "yaml":
                self.highlighter = YAMLHighlighter(self.editor.document())

        # Only if we are explicitly given a cursor position do we add a marker
        if cursor_position >= 0:
            self.editor.highlightLine(cursor_position - 1)
            self.editor.setCursorPosition(cursor_position - 1, 0)
            self.editor.centerCursor()

    def close(self):
        """Performs cleanup actions and returns whether or not it is okay to close this tab"""
        self.file.close()
        return True

    def printPosition(self):  # line: int, column: int):
        """Prints the current editor cursor position"""
        cursor = self.editor.textCursor()
        line = cursor.blockNumber()
        column = cursor.columnNumber()
        self.position_text.setText(f"Line: {line}, Column: {column}")


class ViewFileTab(FileTab):
    """Tab instance for viewing files"""
    def __init__(self, parent):
        super().__init__(parent)

        # No editing!
        self.editor.setReadOnly(True)

        # Layout for open button in a convenient fashion
        self.open_button = QtWidgets.QPushButton(self.button_widget)
        self.open_button.setText("Open")
        self.open_button.clicked.connect(self.open)
        self.open_button.setEnabled(False)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.open_button)

    def openFile(self, filename: str, line_number: int = -1):
        """Loads file"""
        super().openFile(filename, line_number)
        self.open_button.setEnabled(True)

    def close(self):
        """We do not want to be able to close this tab"""
        return False

    def open(self):
        """Opens the current file in a new tab"""
        self.parent().parent().parent().loadFile(self.filename, self.line)


class EditorTab(FileTab):
    """Tab instance for opening and editing a file"""
    def __init__(self, parent):
        super().__init__(parent)

        # Layout to present save button in a nice fashion
        self.save_button = QtWidgets.QPushButton(self.button_widget)
        self.save_button.setText("Save")
        self.save_button.clicked.connect(self.save)
        self.save_button.setEnabled(False)
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_button)

        # Necessary to manage save prompt and button
        self.editor.textChanged.connect(self.handleChanged)

    def openFile(self, filename: str, line_number: int = -1):
        """Loads file into open window"""
        super().openFile(filename, line_number)
        self.save_button.setEnabled(False)

    def handleChanged(self):
        """On file change, enable the save button"""
        # XXX save button always ends up enabled, prompting when no change has been made
        self.save_button.setEnabled(True)

    def save(self):
        """Dumps contents of editor to file"""
        self.file.seek(0)
        self.file.write(self.editor.toPlainText())
        self.file.truncate()
        self.save_button.setEnabled(False)

    def close(self) -> bool:
        """If we have not saved (as indicated by the save button status), prompt user

        Returns whether it is valid to remove the tab or not
        """
        if self.save_button.isEnabled():
            prompt = SaveFileDialog()
            ok = prompt.exec_()
            # Necessary to check here because of "Discard" option
            if prompt.save:
                self.save()
        else:
            ok = True

        self.file.close()
        return ok


class SaveFileDialog(QtWidgets.QDialog):
    """Popup for when a file is closed but not saved"""
    def __init__(self):
        super().__init__()
        self.save = False
        self.setWindowTitle("Save File?")

        button_options = (QtWidgets.QDialogButtonBox.Save
                          | QtWidgets.QDialogButtonBox.Cancel
                          | QtWidgets.QDialogButtonBox.Discard)
        self.button_box = QtWidgets.QDialogButtonBox(button_options)
        self.button_box.clicked.connect(self.onClick)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.button_box)

    def onClick(self, button: QtWidgets.QAbstractButton):
        """Necessary because there isn't an easy signal to attach to for Discard button"""
        role = self.button_box.buttonRole(button)
        if role == self.button_box.AcceptRole:
            self.save = True
            self.accept()
        elif role == self.button_box.DestructiveRole:
            self.accept()
        elif role == self.button_box.RejectRole:
            self.reject()


# CodeEditor to replace QScintill
# (pyside2 has no scintilla wrapper and distribution is a pain with QScintilla)
# "Borrows" from Qt Docs CodeEditor example
class CodeEditor(QtWidgets.QPlainTextEdit):
    """Code editor widget. Implements basic functionality only"""
    def __init__(self, parent):
        super().__init__(parent)

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)

        self.updateLineNumberAreaWidth(0)

    def lineNumberAreaPaintEvent(self, event: QtGui.QPaintEvent):
        """Draws line numbers"""
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtCore.Qt.lightGray)

        # Get geometry
        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(
                self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        # Update per line
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_num + 1)
                painter.setPen(QtCore.Qt.black)
                painter.drawText(0, top, self.line_number_area.width(),
                                 self.fontMetrics().height(),
                                 QtCore.Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_num += 1

    def lineNumberAreaWidth(self) -> int:
        """Specifies the width of the line number area"""
        # find the correct power of 10
        digits = 1
        max_ = max([1, self.blockCount()])
        while (max_ >= 10):
            max_ /= 10
            digits += 1

        return 3 + self.fontMetrics().horizontalAdvance("9") * digits

    def resizeEvent(self, event: QtGui.QResizeEvent):
        """Overrides resize event"""
        super(QtWidgets.QPlainTextEdit, self).resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(),
                         cr.height()))

    def updateLineNumberAreaWidth(self, newBlockCount: int):
        """Updates line number area based on line count"""
        del newBlockCount
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightLine(self, line: int):
        """Highlights a given line"""
        line_colour = QtGui.QColor(QtCore.Qt.yellow).lighter(160)

        selection = QtWidgets.QTextEdit.ExtraSelection()
        selection.format.setBackground(line_colour)
        selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection,
                                     True)
        selection.cursor = QtGui.QTextCursor(
            self.document().findBlockByLineNumber(line))

        self.setExtraSelections([selection])

    def updateLineNumberArea(self, rect: QtCore.QRect, dy: int):
        """Updates size of the line number area"""
        if dy != 0:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.scroll(0, rect.y(), rect)

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def setCursorPosition(self, row: int, column: int):
        """Sets cursor position in document"""
        cursor = QtGui.QTextCursor(self.document().findBlockByLineNumber(row))
        cursor.setPosition(cursor.position() + column)
        self.setTextCursor(cursor)


class LineNumberArea(QtWidgets.QWidget):
    """Widget to show line numbers in custom editor widget,

    Doesn't contain any business logic itself
    """
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event: QtGui.QPaintEvent):
        """Uses the editor to draw the line numbers"""
        self.editor.lineNumberAreaPaintEvent(event)
