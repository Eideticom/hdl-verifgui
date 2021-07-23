###############################################################################
# @file pyVerifGUI/gui/tabs/coverageview.py
# @package pyVerifGUI.gui.tabs.coverageview
# @author David Lenfesty
# @copyright Copyright (c) 2021. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief GUI for managing verilator code coverage reports.
##############################################################################
from qtpy import QtWidgets, QtCore, QtGui
from datetime import date
from typing import Tuple


from pyVerifGUI.gui.models.coverage import CoverageMessageModel, CoverageDiffMessageModel, MessageType
from pyVerifGUI.gui.base_tab import is_tab


from pyVerifGUI.gui.tabs.messageview import MessageViewTab


@is_tab
class CoverageViewTab(MessageViewTab):
    """Coverage view widget implementation. Intended as a widget in a QTabWidget"""
    _name = "coverage"
    _display = "Coverage"
    _tool_tip = "No coverage messages available! Please run coverage parsing from the Overview."

    def _post_init(self):
        super()._post_init(CoverageMessageModel,
                         CoverageDiffMessageModel)
        self.dialog = AddWaiverDialog(self.waiver_widget)
        self.waiver_type = "coverage"
        self.status_name = "parse_coverage"

        self.summary_label.setText("Coverage Run Summary")


    def _verify(self) -> Tuple[bool, str]:
        return (True, "View Coverage Issues")


    def openFile(self):
        """Overriding MessageViewTab implementation because the path needs to be managed"""
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            message = selection_model.selection().indexes()[0].internalPointer()
            filename = (self.config.build_path.resolve()
                        / "coverage_files" / message["file"])
            self.fileOpened.emit(str(filename), message["row"])

    def buildWaiverFromDialog(self) -> dict:
        """Required subclass implementation"""
        return {
            "file": self.dialog.file_text.text(),
            "row": int(self.dialog.row_text.text()),
            "date": date.today().strftime("%Y-%m-%d"),
            "author": self.dialog.author_text.text(),
            "reason": self.dialog.reason_select.currentText(),
            "explanation": self.dialog.explanation_text.toPlainText(),
            "text": self.dialog.text,
            "text_hash": self.dialog.text_hash,
            "waiver": True,
        }

    def buildAddDialog(self, message: MessageType):
        """Required subclass implementation"""
        self.dialog.file_text.setText(message["file"])
        self.dialog.row_text.setText(str(message["row"]))
        self.dialog.row_text.setReadOnly(True)
        self.dialog.explanation_text.setText("")
        self.dialog.text = message["text"]
        self.dialog.text_hash = message["text_hash"]

    def buildEditDialog(self, waiver: MessageType):
        """Required subclass implementation"""
        self.dialog.file_text.setText(waiver["file"])
        self.dialog.row_text.setText(str(waiver["row"]))
        self.dialog.row_text.setReadOnly(True)
        self.dialog.author_text.setText(waiver["author"])
        # TODO set reason select properly
        #self.dialog.reason_select.setCurrentText
        self.dialog.explanation_text.setText(waiver["explanation"])
        self.dialog.text = waiver["text"]
        self.dialog.text_hash = waiver["text_hash"]

    def messageDetails(self, message: MessageType) -> str:
        """Returns text to display about message. Overrides base MessageView implementation"""
        return f"""### Linter Message

{message['file']}: Line {message['row']}.

{message['text']}

Comment: {message['comment']}
"""

    def waiverDetails(self, waiver: MessageType) -> str:
        """Returns text to display about waiver"""
        return f"""
### Waiver

{waiver['file']}: Line {waiver['row']}, waived on {waiver['date']}.

{waiver['text']}

Waiving reason: {waiver['reason']}
"""

    def generateSummary(self) -> str:
        """Generates the summary text"""
        model = self.message_table.model()
        count = len(model.all_messages)
        if count > 0:
            waived_count = len(model.waived_messages)
            unwaived_count = len(model.unwaived_messages)
            waiver_count = len(model.waivers)
            waiver_diff = waiver_count - waived_count
            waived_percent = 100 * (waived_count / count)
            unwaived_percent = 100 * (unwaived_count / count)

            # Match up reason with a different array of the counts of waived messages
            reasons_count = [0] * len(self.dialog.reasons)
            for i in range(len(reasons_count)):
                reasons_count[i] = len([
                    issue for issue in model.waivers
                    if issue["reason"] == self.dialog.reasons[i]
                ])

            try:
                # TODO exception here if tests don't actually clean up
                coverage_count = self.config.status["coverage_total"]
                uncovered_count = self.config.status["uncovered_count"]
                covered_count = coverage_count - uncovered_count
                coverage_percent = round(covered_count / coverage_count * 100, 2)
                waivered_coverage_count = covered_count + waiver_count
                waivered_coverage_percent = round(
                    waivered_coverage_count / coverage_count * 100, 2)
            except ZeroDivisionError:
                # Divide by 0 means no coverage whatsover, so it's incorrect
                return ""

            issue_files = []
            for msg in self.message_table.model().unwaived_messages:
                if msg["file"] not in issue_files:
                    issue_files.append(msg["file"])

            text = f"## Total coverage: ({covered_count}/{coverage_count}) {coverage_percent}%\n\n"
            text += "Waivers:\n"
            for i in range(len(reasons_count)):
                text += f"- {self.dialog.reasons[i]}: {reasons_count[i]}\n"
            text += f"\n## Coverage with waivers: ({waivered_coverage_count}/{coverage_count}) {waivered_coverage_percent}%\n\n"

            text += f"## Total coverage issues: {count}\n\n"
            text += f"{round(waived_percent, 1)}% waived - {waived_count} / {count}\n\n"
            text += f"{round(unwaived_percent, 1)}% unwaived - {unwaived_count} / {count}\n\n"
            if waiver_diff > 1:
                text += f"{waiver_diff} waivers that do not apply!"
            elif waiver_diff == 1:
                text += "1 waiver that does not apply!"

            file_count = 0
            open_file = self.config.build_path.resolve() / "rtlfiles.lst"
            if open_file.exists():
                with open(str(open_file), "r") as f:
                    for _ in f:
                        file_count += 1

                text += f"{file_count} files covered, {len(issue_files)} have issues\n\n"

            try:
                text += f"### Last Run time: {round(self.config.status['coverage_run_time'],1)}s\n\n"
            except KeyError:
                pass

            return text
        else:
            return ""


class AddWaiverDialog(QtWidgets.QDialog):
    """Custom dialog to add a new waiver"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setModal(True)

        self.setWindowTitle("Add Waiver")

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
        self.author_label = QtWidgets.QLabel(self)
        self.author_label.setAlignment(label_alignment)
        self.author_label.setText("Author")
        self.reason_label = QtWidgets.QLabel(self)
        self.reason_label.setAlignment(label_alignment)
        self.reason_label.setText("Reason")
        self.explanation_label = QtWidgets.QLabel(self)
        self.explanation_label.setAlignment(label_alignment)
        self.explanation_label.setText("Explanation")
        self.text_label = QtWidgets.QLabel("Text in File", self)
        self.text_label.setAlignment(label_alignment)

        # Data
        self.file_text = QtWidgets.QLineEdit(self)
        self.file_text.setReadOnly(True)
        self.row_text = QtWidgets.QLineEdit(self)
        self.row_text.setReadOnly(True)
        self.author_text = QtWidgets.QLineEdit(self)
        self.reason_select = QtWidgets.QComboBox(self)
        self.explanation_text = QtWidgets.QTextEdit(self)
        self.text_text = QtWidgets.QLineEdit(self)
        self.text_text.setReadOnly(True)

        # Add pre-built list of reasons
        self.reason_select.setEditable(True)
        self.reasons = [
            "Coverd by Single TC",
            "Unused signal",
            "Unused port",
            "Unreachable state",
            "Unreachable code",
            "Not Required",
            "Other",
        ]
        for reason in self.reasons:
            self.reason_select.addItem(reason)

        # Layout
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.file_label, 0, 0)
        self.layout.addWidget(self.file_text, 0, 1)
        self.layout.addWidget(self.row_label, 1, 0)
        self.layout.addWidget(self.row_text, 1, 1)
        self.layout.addWidget(self.author_label, 2, 0)
        self.layout.addWidget(self.author_text, 2, 1)
        self.layout.addWidget(self.reason_label, 3, 0)
        self.layout.addWidget(self.reason_select, 3, 1)
        self.layout.addWidget(self.explanation_label, 4, 0)
        self.layout.addWidget(self.explanation_text, 4, 1)
        self.layout.addWidget(self.text_label, 5, 0)
        self.layout.addWidget(self.text_text, 5, 1)
        self.layout.addWidget(self.buttonBox, 6, 0, 1, 2)
