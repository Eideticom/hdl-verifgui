"""Collection of Menus for use in the MenuBar"""

__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from qtpy import QtWidgets, QtCore
from pathlib import Path
import subprocess as sp
import shutil

from pyVerifGUI.tasks import task_names


class FileMenu(QtWidgets.QMenu):
    """Custom menu for doing file-based stuff"""

    log_output = QtCore.Signal(str)

    def __init__(self, parent, config):
        super().__init__("File", parent)
        self.config = config

        self.commit_lint = QtWidgets.QAction("Commit Linter Waivers", self)
        self.commit_lint.triggered.connect(self.commitLint)

        self.save_parsed = QtWidgets.QAction("Save parser outputs", self)
        self.save_parsed.triggered.connect(self.saveParsed)

        self.addSection("Git")
        self.addAction(self.commit_lint)
        self.addSection("Outputs")
        self.addAction(self.save_parsed)

        self.commit_dialog = QtWidgets.QDialog()
        self.commit_layout = QtWidgets.QVBoxLayout(self.commit_dialog)
        self.commit_dialog.setWindowTitle("Commiting waiver files")
        self.commit_file = QtWidgets.QLabel(self.commit_dialog)
        self.commit_file.setAlignment(QtCore.Qt.AlignHCenter)
        self.commit_label = QtWidgets.QLabel("Enter Commit Message",
                                             self.commit_dialog)
        self.commit_text = QtWidgets.QLineEdit(self.commit_dialog)
        self.commit_buttons = QtWidgets.QDialogButtonBox(
            QtCore.Qt.Horizontal, self.commit_dialog)
        self.commit_buttons.addButton(self.commit_buttons.Ok)
        self.commit_buttons.addButton(self.commit_buttons.Cancel)
        self.commit_buttons.accepted.connect(self.doCommit)
        self.commit_buttons.accepted.connect(self.commit_dialog.accept)
        self.commit_buttons.rejected.connect(self.commit_dialog.reject)

        self.commit_layout.addWidget(self.commit_file)
        self.commit_layout.addWidget(self.commit_label)
        self.commit_layout.addWidget(self.commit_text)
        self.commit_layout.addWidget(self.commit_buttons)

    def commitLint(self, checked=False):
        """Preps for linter waiver commits"""
        del checked
        filename = self.config.build_path.resolve() / "linter_waivers.yaml"
        if filename.exists():
            self.commit_file.setText(str(filename))
            self.commit_dialog.exec_()

    def doCommit(self):
        """Actually commits files"""
        filename = self.commit_file.text()
        cwd = self.config.core_dir_path
        msg = self.commit_text.text()
        sp.run(["git", "add", "-f", filename], check=True, cwd=cwd)
        sp.run(["git", "commit", "-o", filename, "-m", msg],
               check=True,
               cwd=cwd)

    def saveParsed(self):
        """Opens a dialog to save parsed files elsewhere"""
        if self.config.build is not None and self.config.status[
                task_names.parse]:
            get_dir = QtWidgets.QFileDialog.getExistingDirectory
            path = get_dir(self, "Select Directory to save Parsed Files")
        else:
            QtWidgets.QMessageBox.information(
                self, "Select a Build",
                "Please select a build with completed parsing.")
            return

        if path != "":
            self.log_output.emit(
                f"Saving parsed files from {self.config.build} to {path}")
            parse_dir = f"sv_{self.config.top_module}"
            prev_parse_path = self.config.build_path / parse_dir
            new_parse_path = Path(path) / parse_dir
            try:
                shutil.copytree(str(prev_parse_path), str(new_parse_path))
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Copy Failed!", str(exc))

            prev_list = self.config.build_path / "rtlfiles.lst"
            new_list = Path(path) / "rtlfiles.lst"
            try:
                shutil.copyfile(prev_list, new_list)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self, "Copy Failed!", str(exc))

            self.log_output.emit(f"Copied parse files to {path}")


class ViewMenu(QtWidgets.QMenu):
    """Menu to change different view parameters"""
    def __init__(self, parent):
        super().__init__("View", parent)

        self.clear_log = QtWidgets.QAction("Clear Log Pane", self)
        self.clear_log.triggered.connect(self.clearLog)

        self.clear_command = QtWidgets.QAction("Clear Output Pane", self)
        self.clear_command.triggered.connect(self.clearCommand)

        self.full_filenames = QtWidgets.QAction("Show Full Filenames", self)
        self.full_filenames.setCheckable(True)
        self.full_filenames.setChecked(False)
        self.full_filenames.toggled.connect(self.showFullFilenames)

        self.app = self.parent().parent()

        self.addSection("Output Panes")
        self.addAction(self.app.log_dock.toggleViewAction())
        self.addAction(self.clear_log)
        self.addAction(self.clear_command)
        self.addSection("Messages")
        self.addAction(self.full_filenames)

    def showLog(self, checked=True):
        """Slot to show/hide log output"""
        self.app.logger.log_widget.setVisible(checked)

    def showCommand(self, checked=False):
        """Slot to show/hide command output"""
        self.app.logger.out_widget.setVisible(checked)

    def clearLog(self):
        """Clears log pane"""
        self.app.logger.log_text.clear()

    def clearCommand(self):
        """Clears command output pane"""
        self.app.logger.out_text.clear()

    def showFullFilenames(self, checked=False):
        """Slot to set if we show or hide full filenames"""
        self.app.lint_tab.view_full_filenames = checked


class HelpMenu(QtWidgets.QMenu):
    """Menu for help and application information"""
    def __init__(self, parent):
        super().__init__("Help", parent)
        self.help = QtWidgets.QAction("Show Help Documentation", self)
        self.info = QtWidgets.QAction("Program Information", self)

        self.addAction(self.help)
        self.addAction(self.info)

        self.help_dialog = QtWidgets.QDialog(self)
        self.help_layout = QtWidgets.QGridLayout(self.help_dialog)
        self.help_browser = QtWidgets.QTextBrowser(self.help_dialog)
        self.help_browser.setSearchPaths(["./", "./assets"])
        self.help_backward = QtWidgets.QPushButton("Backwards",
                                                   self.help_dialog)
        self.help_backward.setEnabled(False)
        self.help_forward = QtWidgets.QPushButton("Forwards", self.help_dialog)
        self.help_forward.setEnabled(False)

        # signals
        self.help.triggered.connect(self.displayHelp)
        self.help_browser.historyChanged.connect(self.updateHelpButtons)
        self.help_backward.clicked.connect(self.help_browser.backward)
        self.help_forward.clicked.connect(self.help_browser.forward)

        self.help_layout.addWidget(self.help_browser, 0, 0, 1, 2)
        self.help_layout.addWidget(self.help_backward, 1, 0)
        self.help_layout.addWidget(self.help_forward, 1, 1)

    def displayHelp(self):
        """Displays help content"""
        # TODO make this work when ran from outside the pyVerifGUI folder
        self.help_browser.setSource(QtCore.QUrl("assets/help/main.md"))
        self.help_browser.home()
        self.help_dialog.exec_()

    def updateHelpButtons(self):
        """Updates history buttons"""
        backward = self.help_browser.backwardHistoryCount() > 0
        forward = self.help_browser.forwardHistoryCount() > 0
        self.help_backward.setEnabled(backward)
        self.help_forward.setEnabled(forward)
