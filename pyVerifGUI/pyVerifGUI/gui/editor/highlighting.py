"""Syntax highlighting implementations"""

__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from qtpy import QtGui, QtCore
from typing import Union, Sequence
from collections.abc import Iterable
from collections import namedtuple


class SimpleHighlighter(QtGui.QSyntaxHighlighter):
    """Base class for implementing simple highlighters"""
    Rule = namedtuple('Rule', ['fmt', 'pattern'])
    rules = []

    def addPatterns(self, fmt: QtGui.QTextCharFormat,
                    patterns: Union[str, Sequence[str]]):
        """Adds a list of patterns to the list of rules to be matched against"""
        if isinstance(patterns, Iterable) and type(patterns) is not str:
            for pattern in patterns:
                self.rules.append(
                    self.Rule(fmt, QtCore.QRegularExpression(pattern)))
        elif type(patterns) is str:
            self.rules.append(
                self.Rule(fmt, QtCore.QRegularExpression(patterns)))
        else:
            raise TypeError(
                f"Pattern passed ({patterns}) is not a string or a list of strings!"
            )

    def highlightBlock(self, text: str):
        """Function to highlight given block of text"""
        for rule in self.rules:
            match_iterator = rule.pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(),
                               rule.fmt)

        self.setCurrentBlockState(0)


class SVHighlighter(SimpleHighlighter):
    """Basic SystemVerilog Syntax Highlighter"""
    def __init__(self, parent):
        super().__init__(parent)

        # TODO make this regex cleaner
        # Variable names
        name_format = QtGui.QTextCharFormat()
        name_format.setForeground(QtCore.Qt.blue)
        # I think I may be abusing regexps here
        self.addPatterns(
            name_format,
            "\\b[A-Za-z][A-Za-z0-9_]+(?=[\\h]*[\\(\\[\\<\\=;,\\|\\\&\\+\\)\\]\\H])"
        )

        # Keywords
        # XXX Maybe move these elsewhere?
        keyword_format = QtGui.QTextCharFormat()
        keyword_format.setForeground(QtCore.Qt.darkBlue)
        keyword_format.setFontWeight(QtGui.QFont.Bold)
        keyword_patterns = [
            "\\balways\\b",
            "\\bassign\\b",
            "\\bcase\\b",
            "\\bdefault\\b",
            "\\bdefparam\\b",
            "\\bedge\\b",
            "\\belse\\b",
            "\\bevent\\b",
            "\\bfor\\b",
            "\\bforce\\b",
            "\\bforever\\b",
            "\\bfunction\\b",
            "\\bif\\b",
            "\\bifnone\\b",
            "\\balways_ff\\b",
            "\\balways_comb\\b",
            "\\binitial\\b",
            "\\bjoin\\b",
            "\\blarge\\b",
            "\\bmacromodule\\b",
            "\\bmodule\\b",
            "\\bnegedge\\b",
            "\\bnor\\b",
            "\\bnot\\b",
            "\\bor\\b",
            "\\bparameter\\b",
            "\\bpmos\\b",
            "\\bposedge\\b",
            "\\bprimitive\\b",
            "\\bpull0\\b",
            "\\bpullup\\b",
            "\\bpulldown\\b",
            "\\brelease\\b",
            "\\brealtime\\b",
            "\\brelease\\b",
            "\\brepeat\\b",
            "\\brtran\\b",
            "\\btable\\b",
            "\\btask\\b",
            "\\btime\\b",
            "\\btran\\b",
            "\\bvectored\\b",
            "\\bwait\\b",
            "\\bwand\\b",
            "\\bwhile\\b",
            "\\bpackage\\b",
            "\\bendpackage\\b",
            "\\bendcase\\b",
            "\\bendmodule\\b",
            "\\bendfunction\\b",
            "\\bendprimitive\\b",
            "\\bendspecify\\b",
            "\\bendtable\\b",
            "\\bendtask\\b",
            "\\bgenerate\\b",
            "\\bendgenerate\\b",
        ]
        self.addPatterns(keyword_format, keyword_patterns)

        # variable types
        var_format = QtGui.QTextCharFormat()
        var_format.setForeground(QtCore.Qt.darkRed)
        var_format.setFontWeight(QtGui.QFont.Bold)
        var_patterns = [
            "\\blogic\\b", "\\bwire\\b", "\\binteger\\b", "\\blocalparam\\b",
            "\\breal\\b", "\\breg\\b", "\\btrireg\\b"
        ]
        self.addPatterns(var_format, var_patterns)

        # input, output, inout
        io_format = QtGui.QTextCharFormat()
        io_format.setForeground(QtCore.Qt.darkMagenta)
        io_format.setFontWeight(QtGui.QFont.Bold)
        io_patterns = ["\\binput\\b", "\\boutput\\b", "\\binout\\b"]
        self.addPatterns(io_format, io_patterns)

        # Module connections
        module_conn_format = QtGui.QTextCharFormat()
        module_conn_format.setForeground(QtCore.Qt.darkRed)
        self.addPatterns(module_conn_format, "\\.[A-Za-z0-9_]+")

        # "Begin", and "end" should be different than most keywords
        block_format = QtGui.QTextCharFormat()
        block_format.setForeground(QtCore.Qt.darkCyan)
        block_patterns = ["\\bbegin\\b", "\\bend\\b"]
        self.addPatterns(block_format, block_patterns)

        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtCore.Qt.darkGreen)
        self.addPatterns(comment_format, ["//[^\n]*", "/\*.*/"])

        # Compiler directives
        compiler_format = QtGui.QTextCharFormat()
        compiler_format.setForeground(QtCore.Qt.darkMagenta)
        compiler_format.setFontWeight(QtGui.QFont.Bold)
        self.addPatterns(compiler_format, "`[A-Za-z]+\\b")


class YAMLHighlighter(SimpleHighlighter):
    """Does some simple YAML highlighting"""
    def __init__(self, parent):
        super().__init__(parent)

        bool_format = QtGui.QTextCharFormat()
        bool_format.setForeground(QtCore.Qt.darkMagenta)
        self.addPatterns(bool_format, ["\\btrue\\b", "\\bfalse\\b"])

        tag_format = QtGui.QTextCharFormat()
        tag_format.setForeground(QtCore.Qt.blue)
        self.addPatterns(tag_format, "\\b[A-Za-z0-9_]+(?=\\:)")

        num_format = QtGui.QTextCharFormat()
        num_format.setForeground(QtCore.Qt.darkCyan)
        self.addPatterns(num_format, "\\b[0-9\\.]+")

        str_format = QtGui.QTextCharFormat()
        str_format.setForeground(QtCore.Qt.darkRed)
        self.addPatterns(str_format, "\".*\"")

        comment_format = QtGui.QTextCharFormat()
        comment_format.setForeground(QtCore.Qt.darkGreen)
        self.addPatterns(comment_format, "\\#[^\n]*")
