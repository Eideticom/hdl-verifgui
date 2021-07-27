###############################################################################
# @file pyVerifGUI/gui/tabs/lintview.py
# @package pyVerifGUI.gui.tabs.lintview
# @author David Lenfesty
# @copyright    Copyright (c) 2020. Eidetic Communications Inc.
#               All rights reserved
#
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#            modified versions.
#
# @brief Class definitions to display linter view tab
##############################################################################

from qtpy import QtWidgets, QtCore, QtGui
from oyaml import safe_load
from datetime import date
from typing import Tuple
import shutil

from pyVerifGUI.gui.models import LintMessageModel, DiffLintMessageModel, MessageType
from pyVerifGUI.gui.base_tab import is_tab
from pyVerifGUI.tasks.lint import LintTask

from pyVerifGUI.gui.tabs.messageview import MessageViewTab


@is_tab
class LintViewTab(MessageViewTab):
    _name = "lint"
    _display = "Linter"
    _placement = 2
    _tool_tip = "No lint ran yet!"

    """Provides a view of the linter output"""
    def _post_init(self):
        super()._post_init(LintMessageModel, DiffLintMessageModel)
        self.dialog = AddWaiverDialog(self.waiver_widget)
        self.waiver_type = "linter"
        self.status_name = LintTask._name
        self.summary_label.setText("Linter Summary")

        # add "open message URL action to context menu"
        self.view_linter_warning_act = QtWidgets.QAction(
            "Explain Linter Warning", self)
        self.view_linter_warning_act.triggered.connect(self.viewWarning)
        self.context_menu.addSection("Info")
        self.context_menu.addAction(self.view_linter_warning_act)

    def _verify(self) -> Tuple[bool, str]:
        if self.config.config.get("working_dir") is None:
            return (False, "Configuration does not have working directory!")
        if self.config.config.get("rtl_dirs") is None:
            return (False, "No sources specified")

        return (True, "")

    def viewWarning(self):
        """Opens a link to the selected warning in your browser"""
        selection_model = self.message_table.selectionModel()
        if selection_model is not None:
            if selection_model.hasSelection():
                message = selection_model.selectedRows()[0].internalPointer()
                url = QtCore.QUrl(
                    f"https://veripool.org/projects/verilator/wiki/Manual-verilator#{message['type']}"
                )
                # open url in default browser
                QtGui.QDesktopServices.openUrl(url)

    def buildWaiverFromDialog(self) -> dict:
        """Required subclass implementation"""
        return {
            "file": self.dialog.file_text.text(),
            "lineno": int(self.dialog.row_text.text()),
            "type": self.dialog.type_text.text(),
            "author": self.dialog.author_text.text(),
            "date": date.today().strftime("%Y-%m-%d"),
            "reason": self.dialog.reason_text.toPlainText(),
            "text_hash": self.dialog.text_hash,
            "text": self.dialog.text_text.text(),
            "waiver": True,
            "reviewed": False,
        }

    def buildAddDialog(self, message: MessageType):
        """Required subclass implementation"""
        self.dialog.file_text.setText(message["file"])
        self.dialog.row_text.setText(str(message["lineno"]))
        self.dialog.row_text.setReadOnly(True)
        self.dialog.type_text.setText(message["type"])
        self.dialog.reason_text.setText("")
        self.dialog.text_hash = message["text_hash"]
        self.dialog.text_text.setText(message["text"])

    def buildEditDialog(self, waiver: MessageType):
        """Required subclass implementation"""
        self.dialog.file_text.setText(waiver["file"])
        self.dialog.row_text.setText(str(waiver["lineno"]))
        self.dialog.row_text.setReadOnly(True)
        self.dialog.type_text.setText(waiver["type"])
        self.dialog.author_text.setText(waiver["author"])
        self.dialog.reason_text.setPlainText(waiver["reason"])
        self.dialog.text_text.setText(waiver["text"])
        self.dialog.text_hash = waiver["text_hash"]

    def generateSummary(self) -> str:
        """Generates the summary text"""
        model = self.message_table.model()
        count = len(model.all_messages)

        if not self.config.build:
            return ""

        # Load in any verilator errors
        linter_errors_path = self.config.build_path.resolve() / "linter_errors.yaml"
        if linter_errors_path.exists():
            with open(str(linter_errors_path), "r") as f:
                errors = safe_load(f)
        else:
            errors = []

        text = ""

        # Conditionally print any verilator errors
        if errors:
            text += f"## Verilator errors:\n\n"
            for err in errors:
                text += f"- {err}\n"
            text += "\n"

        if count > 0:
            waived_count = len(model.waived_messages)
            unwaived_count = len(model.unwaived_messages)
            waiver_count = len(model.waivers)
            waiver_diff = waiver_count - waived_count
            waived_percent = 100 * (waived_count / count)
            unwaived_percent = 100 * (unwaived_count / count)

            file_count = 0
            open_file = str(self.config.build_path.resolve() / "rtlfiles.lst")
            with open(open_file, "r") as f:
                for _ in f:
                    file_count += 1

            text += f"## Total linting issues: {count}\n\n"
            text += f"{round(waived_percent, 1)}% waived - {waived_count} / {count}\n\n"
            text += f"{round(unwaived_percent, 1)}% unwaived - {unwaived_count} / {count}\n\n"
            if waiver_diff > 1:
                text += f"{waiver_diff} waivers that do not apply!\n\n"
            elif waiver_diff == 1:
                text += "1 waiver that does not apply!\n\n"
            text += f"{file_count} files linted\n\n"

        return text


class AddWaiverDialog(QtWidgets.QDialog):
    """Custom dialog to add a new waiver"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Add Waiver")
        self.setModal(True)

        button_options = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(button_options)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        label_alignment = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight

        # Labels
        self.file_label = QtWidgets.QLabel(self)
        self.file_label.setAlignment(label_alignment)
        self.file_label.setText("File")
        self.row_label = QtWidgets.QLabel(self)
        self.row_label.setAlignment(label_alignment)
        self.row_label.setText("Line")
        self.type_label = QtWidgets.QLabel(self)
        self.type_label.setAlignment(label_alignment)
        self.type_label.setText("Warning Type")
        self.author_label = QtWidgets.QLabel(self)
        self.author_label.setAlignment(label_alignment)
        self.author_label.setText("Author")
        self.reason_label = QtWidgets.QLabel(self)
        self.reason_label.setAlignment(label_alignment)
        self.reason_label.setText("Reason")
        self.text_label = QtWidgets.QLabel("Text in File", self)
        self.text_label.setAlignment(label_alignment)

        # Data
        self.file_text = QtWidgets.QLineEdit(self)
        self.file_text.setReadOnly(True)
        self.row_text = QtWidgets.QLineEdit(self)
        self.row_text.setReadOnly(True)
        self.type_text = QtWidgets.QLineEdit(self)
        self.author_text = QtWidgets.QLineEdit(self)
        self.reason_text = QtWidgets.QTextEdit(self)
        self.text_text = QtWidgets.QLineEdit(self)
        self.text_text.setReadOnly(True)

        # Layout
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.file_label, 0, 0)
        self.layout.addWidget(self.file_text, 0, 1)
        self.layout.addWidget(self.row_label, 1, 0)
        self.layout.addWidget(self.row_text, 1, 1)
        self.layout.addWidget(self.type_label, 2, 0)
        self.layout.addWidget(self.type_text, 2, 1)
        self.layout.addWidget(self.author_label, 3, 0)
        self.layout.addWidget(self.author_text, 3, 1)
        self.layout.addWidget(self.reason_label, 4, 0)
        self.layout.addWidget(self.reason_text, 4, 1)
        self.layout.addWidget(self.text_label, 5, 0)
        self.layout.addWidget(self.text_text, 5, 1)
        self.layout.addWidget(self.buttonBox, 6, 0, 1, 2)
