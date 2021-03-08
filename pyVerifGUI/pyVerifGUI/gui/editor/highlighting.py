###############################################################################
# @file pyVerifGUI/gui/editor/highlighting.py
# @package pyVerifGUI.gui.editor.highlighting
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Implementations for regex-based syntax highlighting
##############################################################################

from qtpy import QtGui, QtCore
from typing import Union, Sequence
from collections.abc import Iterable
from collections import namedtuple

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatter import Formatter as pyg_Formatter

import time

def color_converter(color):
    """Converts hex-style color value to QColor object"""
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return QtGui.QColor(r, g, b)

class Formatter(pyg_Formatter):
    def __init__(self):
        super().__init__()
        self.data = []

        self.styles = {}
        for token, style in self.style:
            format = QtGui.QTextCharFormat()

            if style["color"]:
                format.setForeground(color_converter(style["color"]))
            if style["bgcolor"]:
                format.setBackground(color_converter(style["bgcolor"]))
            if style["bold"]:
                format.setFontWeight(QtGui.QFont.Bold)
            if style["italic"]:
                format.setFontItalic(True)
            if style["underline"]:
                format.setFontUnderline(True)
            
            self.styles[str(token)] = format

    def format(self, tokensource, outfile):
        self.data = []

        offset = 0
        for ttype, value in tokensource:
            l = len(value)
            t = str(ttype)
            self.data.append((offset, l, t))

            offset += l

class Highlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent, language):
        super().__init__(parent)

        self.formatter = Formatter()
        self.lexer = get_lexer_by_name(language)
        self.highlighted = False

    def highlightBlock(self, text: str):
        # Only highlight once
        # TODO ideally there's a way to stream into the lexer
        if not self.highlighted:
            highlight(self.document().toPlainText() + '\n', self.lexer, self.formatter)
            self.highlighted = True

        offset = self.currentBlock().position()
        end = offset + len(text)

        # Only highlight in the current block
        # TODO doesn't seem to highlight lots of objects.
        #      is that the lexer or is that something I'm doing wrong?
        for h in self.formatter.data:
            if h[0] > offset and h[0] < end:
                self.setFormat(h[0] - offset, h[1], self.formatter.styles[h[2]])
