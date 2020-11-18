###############################################################################
# @file pyVerifGUI/gui/tabs/messageview.py
# @package pyVerifGUI.gui.tabs.messageview
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Base class for a standardized message view tab
##############################################################################

from qtpy import QtWidgets, QtCore, QtGui
from oyaml import safe_load, dump
import shutil
import copy
from typing import Sequence

from pyVerifGUI.gui.editor import Editor
from pyVerifGUI.gui.models import MessageType, MessageListType
from pyVerifGUI.gui.models.message import Messages
from pyVerifGUI.gui.base_tab import Tab

class MessageViewTab(Tab):
    """Base class to view messages with associated waivers"""

    # Signal emitted when a file is opened
    fileOpened = QtCore.Signal(str, int)

    def _post_init(self, messageModel: Messages,
                 diffMessageModel: Messages):
        self.messageModel = messageModel
        self.diffMessageModel = diffMessageModel

        self.dialog = None
        self.old_waiver = None
        self.waiver_type = ""
        self.status_name = ""

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setObjectName("layout")

        # Two main widgets, so we can resize
        self.message_widget = QtWidgets.QWidget(self)
        self.message_layout = QtWidgets.QVBoxLayout(self.message_widget)
        self.message_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical, self.message_widget)
        self.extra_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical, self)

        # Message filtering buttons
        self.message_filter_widget = QtWidgets.QWidget(self.message_splitter)
        self.message_filter_layout = QtWidgets.QHBoxLayout(
            self.message_filter_widget)
        self.message_show_all = QtWidgets.QRadioButton(
            self.message_filter_widget)
        self.message_show_all.setText("All Messages")
        self.message_show_all.clicked.connect(self.onFilterChange)
        self.message_show_all.setChecked(True)
        self.message_show_unwaived = QtWidgets.QRadioButton(
            self.message_filter_widget)
        self.message_show_unwaived.setText("Not Waived")
        self.message_show_unwaived.clicked.connect(self.onFilterChange)
        self.message_show_waived = QtWidgets.QRadioButton(
            self.message_filter_widget)
        self.message_show_waived.setText("Waived")
        self.message_show_waived.clicked.connect(self.onFilterChange)
        self.message_show_waivers = QtWidgets.QRadioButton(
            self.message_filter_widget)
        self.message_show_waivers.setText("Waivers Only")
        self.message_show_waivers.clicked.connect(self.onFilterChange)
        self.message_show_orphans = QtWidgets.QRadioButton(
            "Orphaned Waivers", self.message_filter_widget)
        self.message_show_orphans.hide()
        self.message_show_orphans.setStyleSheet("""
            background-color: rgb(255, 100, 100);
            border-radius: 5px;
            border: 1px solid black
            """)
        self.message_show_orphans.clicked.connect(self.onFilterChange)
        self.message_filter_layout.addStretch()
        self.message_filter_layout.addWidget(self.message_show_all)
        self.message_filter_layout.addWidget(self.message_show_unwaived)
        self.message_filter_layout.addWidget(self.message_show_waived)
        self.message_filter_layout.addWidget(self.message_show_waivers)
        self.message_filter_layout.addWidget(self.message_show_orphans)

        # Main message table
        self.message_table = QtWidgets.QTableView(self.message_splitter)
        self.message_table.setObjectName("message_table")
        self.message_table.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)
        self.message_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.message_table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.message_table.setHorizontalScrollMode(
            self.message_table.ScrollPerPixel)
        self.message_table.doubleClicked.connect(self.addOrEditWaiver)

        # Linter Message Details view
        self.text = QtWidgets.QTextEdit(self.message_splitter)
        self.text.setReadOnly(True)

        # Tie message widget together with layout
        self.message_layout.addWidget(self.message_filter_widget)
        self.message_splitter.addWidget(self.message_table)
        self.message_splitter.setStretchFactor(1, 2)
        self.message_splitter.addWidget(self.text)
        self.message_splitter.setStretchFactor(2, 1)
        self.message_layout.addWidget(self.message_splitter)

        # "Extra" function tabs
        self.extra_tabs = QtWidgets.QTabWidget(self.extra_splitter)
        self.editor_tab = Editor(self.extra_tabs, self.config)
        self.extra_tabs.addTab(self.editor_tab, "Editor")
        self.diff_tab = DiffViewTab(self.extra_tabs)
        self.extra_tabs.addTab(self.diff_tab, "Diff View")
        self.orphan_tab = OrphanTab(self.extra_tabs, self.config,
                                    self.messageModel)
        self.orphan_tab.orphanUpdate.connect(self.updateOrphan)
        self.extra_tabs.addTab(self.orphan_tab, "Orphan Cleanup")
        self.extra_tabs.setTabEnabled(self.extra_tabs.indexOf(self.orphan_tab),
                                      False)

        # Summary widget
        self.summary_widget = QtWidgets.QWidget(self.text)
        self.summary_layout = QtWidgets.QVBoxLayout(self.summary_widget)
        self.summary_label = QtWidgets.QLabel(self.summary_widget)
        self.summary_text = QtWidgets.QTextEdit(self.summary_widget)
        self.summary_text.setReadOnly(True)
        self.summary_layout.addWidget(self.summary_label)
        self.summary_layout.addWidget(self.summary_text)
        self.message_splitter.addWidget(self.summary_widget)
        self.message_splitter.setStretchFactor(3, 1)

        # Tie together extra functions
        self.extra_splitter.addWidget(self.extra_tabs)
        self.extra_splitter.setStretchFactor(0, 2)

        # Waiver management buttons
        self.waiver_widget = QtWidgets.QWidget(self)
        self.waiver_layout = QtWidgets.QHBoxLayout(self.waiver_widget)
        self.mark_legitimate = QtWidgets.QPushButton("Toggle Legitimate",
                                                     self.waiver_widget)
        self.mark_legitimate.clicked.connect(self.markLegitimate)
        self.waiver_edit = QtWidgets.QPushButton("Add/Edit Waiver",
                                                 self.waiver_widget)
        self.waiver_edit.clicked.connect(self.addOrEditWaiver)
        self.waiver_remove = QtWidgets.QPushButton(self.waiver_widget)
        self.waiver_remove.setText("Remove Waiver")
        self.waiver_remove.clicked.connect(self.waiverRemove)
        self.orphan_update = QtWidgets.QPushButton("Update Orphan")
        self.orphan_update.clicked.connect(self.handleOrphanUpdate)
        self.orphan_update.setEnabled(False)
        self.waiver_layout.addStretch()
        self.waiver_layout.addWidget(self.mark_legitimate)
        self.waiver_layout.addWidget(self.waiver_edit)
        self.waiver_layout.addWidget(self.waiver_remove)
        self.waiver_layout.addWidget(self.orphan_update)

        # Layout configuration
        self.hz_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Horizontal, self)
        self.hz_splitter.addWidget(self.message_widget)
        self.hz_splitter.addWidget(self.extra_splitter)
        self.layout.addWidget(self.hz_splitter)
        self.layout.setStretch(0, 1)
        self.layout.addWidget(self.waiver_widget)

        # Dialogs
        self.empty_fields_dialog = QtWidgets.QMessageBox()
        self.empty_fields_dialog.setText("Empty fields are not permitted!")
        self.no_waiver_dialog = QtWidgets.QMessageBox()
        self.no_waiver_dialog.setText(
            "Nothing selected or selection is not a waiver!")
        self.select_build_dialog = QtWidgets.QMessageBox()
        self.select_build_dialog.setText("Please select a build first!")

        self.edit_comment_dialog = QtWidgets.QDialog(self)
        self.edit_comment_dialog.setWindowTitle("Edit Comment")
        self.edit_comment_dialog.layout = QtWidgets.QVBoxLayout(
            self.edit_comment_dialog)
        self.edit_comment_dialog.comment = QtWidgets.QTextEdit(
            self.edit_comment_dialog)
        self.edit_comment_dialog.buttons = QtWidgets.QDialogButtonBox(
            self.edit_comment_dialog)
        self.edit_comment_dialog.buttons.addButton(
            QtWidgets.QDialogButtonBox.Ok)
        self.edit_comment_dialog.buttons.addButton(
            QtWidgets.QDialogButtonBox.Cancel)
        self.edit_comment_dialog.buttons.accepted.connect(
            self.edit_comment_dialog.accept)
        self.edit_comment_dialog.buttons.rejected.connect(
            self.edit_comment_dialog.reject)
        self.edit_comment_dialog.layout.addWidget(
            self.edit_comment_dialog.comment)
        self.edit_comment_dialog.layout.addWidget(
            self.edit_comment_dialog.buttons)

        # Context menu
        self.open_file_act = QtWidgets.QAction("Open File", self)
        self.open_file_act.triggered.connect(self.openFile)
        self.open_file_act.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        self.mark_legitimate_act = QtWidgets.QAction("Toggle Legitimate", self)
        self.mark_legitimate_act.setShortcut(QtGui.QKeySequence("Ctrl+L"))
        self.mark_legitimate_act.triggered.connect(self.markLegitimate)
        self.edit_waiver_act = QtWidgets.QAction("Add/Edit Waiver", self)
        self.edit_waiver_act.triggered.connect(self.addOrEditWaiver)
        self.edit_waiver_act.setShortcut(QtGui.QKeySequence("Ctrl+W"))
        self.remove_waiver_act = QtWidgets.QAction("Remove Waiver", self)
        self.remove_waiver_act.triggered.connect(self.waiverRemove)
        self.edit_comment_act = QtWidgets.QAction("Edit Comment", self)
        self.edit_comment_act.triggered.connect(self.editComment)
        self.edit_comment_act.setShortcut(QtGui.QKeySequence("Ctrl+E"))
        self.context_menu = QtWidgets.QMenu(self)
        self.context_menu.addSection("Message Management")
        self.context_menu.addAction(self.mark_legitimate_act)
        self.context_menu.addAction(self.edit_waiver_act)
        self.context_menu.addAction(self.remove_waiver_act)
        self.context_menu.addAction(self.edit_comment_act)
        self.context_menu.addSection("File")
        self.context_menu.addAction(self.open_file_act)

        self.addAction(self.open_file_act)
        self.addAction(self.mark_legitimate_act)
        self.addAction(self.edit_waiver_act)
        self.addAction(self.edit_comment_act)

        # Signal connections
        self.fileOpened.connect(self.editor_tab.loadFile)
        self.orphan_tab.fileOpened.connect(self.openOrphanFile)

        self._view_full_filenames = False

    @property
    def view_full_filenames(self):
        """Returns if model is set to view filenames"""
        model = self.message_table.model()
        if model is not None:
            self.view_full_filenames = self._view_full_filenames

        return self._view_full_filenames

    @view_full_filenames.setter
    def view_full_filenames(self, view: bool):
        """Sets model filenames"""
        self._view_full_filenames = view
        model = self.message_table.model()
        if model is not None:
            model.beginResetModel()
            model.view_full_filenames = view
            model.endResetModel()

    def showEditor(self):
        """Switch extra display tabs to show editor to user."""
        self.extra_tabs.setCurrentWidget(self.editor_tab)
        self.extra_tabs.tabBar().setCurrentIndex(
            self.extra_tabs.currentIndex())

    def openOrphanFile(self, filename: str, line_num: int):
        """Opens file and switches to that tab"""
        self.editor_tab.loadFile(filename, line_num)

        self.showEditor()

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        """Custom context menu"""
        selection_model = self.message_table.selectionModel()
        if selection_model is not None:
            # Edit/remove should not be accessible if selection is not a waiver
            has_waiver = False
            if selection_model.hasSelection():
                message = selection_model.selection().indexes(
                )[0].internalPointer()
                if self.checkIfMessage(message):
                    if self.message_table.model().findWaiver(
                            message) is not None:
                        has_waiver = True
                    else:
                        has_waiver = False
                else:
                    has_waiver = True
            else:
                has_waiver = False
            self.remove_waiver_act.setEnabled(has_waiver)

            self.context_menu.exec_(event.globalPos())

    def openFile(self):
        """Opens file based on selected message"""
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            message = selection_model.selection().indexes()[0].internalPointer(
            )

            self.fileOpened.emit(message["file"], message["row"])

    def getMessageSelection(self):
        """Gets the selected message. Returns the message or None if there is nothing selected"""
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            return selection_model.selection().indexes()[0].internalPointer()
        else:
            return None

    def buildWaiverFromDialog(self) -> dict:
        """Required to implement in subclass"""
        raise NotImplementedError

    def dumpMessages(self, model: Messages):
        """Save any modifications to messages"""
        dump(
            model.all_messages.messages,
            open(self.config.build_path / f"{self.waiver_type}_messages.yaml",
                 "w"))

    def dumpWaivers(self, model: Messages):
        """Write list of waivers to file"""
        if self.waiver_type == "":
            raise NotImplementedError

        dump(
            model.waivers.messages,
            open(self.config.build_path / f"{self.waiver_type}_waivers.yaml",
                 "w"))

    def buildAddDialog(self, message: MessageType):
        """Required to implement in subclass

        Builds a dialog to add a waiver, based on the currently selected waiver,
        if there is one
        """
        raise NotImplementedError

    def markLegitimate(self, checked=False):
        """Marks a message as legitimate"""
        del checked
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            message = selection_model.selection().indexes()[0].internalPointer(
            )
            if self.checkIfMessage(message):
                # toggles legitimate status
                message.update({"legitimate": not message["legitimate"]})
                self.dumpMessages(self.message_table.model())
                self.modelUpdate()

    def addOrEditWaiver(self, checked=False):
        """Common handler for dealing with adding or editing waivers for a message"""
        del checked
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            message = selection_model.selection().indexes()[0].internalPointer(
            )
            if self.checkIfMessage(message):
                waiver = self.message_table.model().findWaiver(message)
                if waiver is None:
                    # No waiver, so we need to add a waiver
                    self.waiverAdd()
                else:
                    # we do have a waiver, so edit it
                    self.waiverEdit()
            else:
                self.waiverEdit()

    def waiverAdd(self, checked=False):
        """Called when adding a waiver"""
        del checked
        message = self.getMessageSelection()
        message_valid = message is not None and not self.message_show_waivers.isChecked(
        )
        if self.config.build is not None:
            if message_valid:
                self.dialog.row_text.setReadOnly(False)
                if self.config.arguments.user is not None:
                    self.dialog.author_text.setText(self.config.arguments.user)

                self.buildAddDialog(message)
                self.dialog.finished.connect(self.waiverAddCB)
                self.dialog.open()
        else:
            self.select_build_dialog.exec_()

    def waiverAddCB(self, r: int):
        """Handler for once the dialog to add a waiver exits"""
        # Do nothing on rejected
        if not r:
            return

        waiver = self.buildWaiverFromDialog()

        # Fail on any empty string
        if any(value == "" for value in waiver.values()):
            self.empty_fields_dialog.exec_()
            return

        # convenience for lookups later
        model = self.message_table.model()

        # Check if we have multiple selections, if we do, then manage adding waivers properly
        rows_selected = self.message_table.selectionModel().selectedRows()
        if len(rows_selected) > 1:
            for row in rows_selected:
                message = row.internalPointer()
                # Check if message already has a waiver
                if model.findWaiver(message) is not None:
                    # message has a waiver, skip it
                    continue

                ## Make a copy of the waiver to edit
                # These fields are the fields matched for messages/waivers,
                # so we can just make these match each message to bulk add.
                waiver_ = waiver.copy()
                waiver_["file"] = message["file"]
                waiver_["row"] = message["row"]
                waiver_["text_hash"] = message["text_hash"]

                model.addWaiver(waiver_)
        else:
            model.addWaiver(waiver)

        # Dump waivers to disk
        self.dumpWaivers(model)
        self.viewUpdate()
        self.dialog.finished.disconnect()

    def buildEditDialog(self, waiver: MessageType):
        """Required to implement in subclass

        Builds the dialog for editing a selected waiver.
        """
        raise NotImplementedError

    def waiverEdit(self, checked=False):
        """Edit a selected waiver"""
        del checked
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            waiver = selection_model.selection().indexes()[0].internalPointer()
            if self.checkIfMessage(waiver):
                waiver = self.message_table.model().findWaiver(waiver)
            self.old_waiver = waiver

            self.buildEditDialog(waiver)

            self.dialog.finished.connect(self.waiverEditCB)
            self.dialog.open()
            return

        self.no_waiver_dialog.exec_()

    def waiverEditCB(self, r: int):
        """Stores edit"""
        if not r:
            return

        waiver = self.buildWaiverFromDialog()

        if any(value == "" for value in waiver.values()):
            self.empty_fields_dialog.exec_()
            return

        model = self.message_table.model()
        model.updateWaiver(self.old_waiver, waiver)
        self.dumpWaivers(model)
        self.viewUpdate()
        self.dialog.finished.disconnect()

    def waiverRemove(self):
        """Called when removing waiver. Generic enough to be implemented here"""
        waiver = self.getMessageSelection()
        # checkIfMessage should return false if it is a waiver
        if waiver is None or self.checkIfMessage(waiver):
            self.no_waiver_dialog.exec_()
            return

        msg = QtWidgets.QMessageBox()
        msg.setText("Confirm removing waiver.")
        msg.setInformativeText(f"In {waiver['file']}, on line {waiver['row']}")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok
                               | QtWidgets.QMessageBox.Cancel)
        msg.setDefaultButton(QtWidgets.QMessageBox.Cancel)

        model = self.message_table.model()
        model.removeWaiver(waiver)
        self.dumpWaivers(model)
        self.viewUpdate()

    def editComment(self):
        """Called when editing a message comment"""
        message = self.getMessageSelection()
        if message is None:
            return

        self.edit_comment_dialog.comment.setText(message["comment"])

        ok = self.edit_comment_dialog.exec_()
        if ok:
            message["comment"] = self.edit_comment_dialog.comment.toPlainText()
            self.dumpMessages(self.message_table.model())
            self.displayMessageDetails()

    def onSelection(self, current: QtCore.QItemSelection,
                    previous: QtCore.QItemSelection):
        """Slot for handling selection and filtering based on orphans"""
        del previous

        selection = current.internalPointer()

        # Update orphan tab
        if self.message_show_orphans.isChecked():
            self.orphan_tab.modelUpdate(
                self.message_table.model().unwaived_messages.messages,
                selection["file"])
        else:
            self.orphan_tab.modelUpdate([], "")

        # Update editor
        self.editor_tab.viewFile(selection["file"], selection["row"])

    def handleOrphanUpdate(self, checked=False):
        """Slot to handle clicking orphan update button"""
        del checked
        self.orphan_tab.updateOrphan()

    def updateOrphan(self, message: MessageType):
        """Slot that updates an existing orphan with new information"""
        # what needs to change:
        # line num, text, text_hash
        selection_model = self.message_table.selectionModel()
        if not selection_model.hasSelection():
            # Don't do anything if you don't have anything selected
            return

        # Update values in waiver
        waiver = selection_model.currentIndex().internalPointer()
        waiver.update({
            "row": message["row"],
            "text_hash": message["text_hash"],
        })

        # Implement changes
        self.dumpWaivers(self.message_table.model())
        self.modelUpdate()

    def onFilterChange(self, checked=False):
        """Slot for handling updates to message view filters"""
        del checked

        # Update orphan tab view
        orphan_index = self.extra_tabs.indexOf(self.orphan_tab)
        if self.message_show_orphans.isChecked():
            self.extra_tabs.setTabEnabled(orphan_index, True)
            self.extra_tabs.setCurrentWidget(self.orphan_tab)
        else:
            self.extra_tabs.setTabEnabled(orphan_index, False)
            self.extra_tabs.setCurrentWidget(self.editor_tab)

        self.extra_tabs.tabBar().setCurrentIndex(
            self.extra_tabs.currentIndex())

        self.viewUpdate()

    def filterLints(self):
        """Selects the appropriately filtered message types"""
        model = self.message_table.model()
        diff_model = self.diff_tab.table.model()
        self.orphan_update.setEnabled(False)
        if self.message_show_unwaived.isChecked():
            selection = "unwaived"
        elif self.message_show_waived.isChecked():
            selection = "waived"
        elif self.message_show_waivers.isChecked():
            selection = "waivers"
        elif self.message_show_orphans.isChecked():
            selection = "orphans"
            self.orphan_update.setEnabled(True)
        else:
            selection = "all"

        model.selectMessages(selection)
        diff_model.selectMessages(selection)

    def checkIfMessage(self, message: MessageType) -> bool:
        """Returns true if message, false if waiver"""
        return not message["waiver"]

    def messageDetails(self, message: MessageType) -> str:
        """Returns text to display about message"""
        return f"""### Linter Message

{message['file']}: Line {message['row']}, column {message['column']}.

{message['type']}: {message['text']}

Comment: {message['comment']}
"""

    def waiverDetails(self, waiver: MessageType) -> str:
        """Returns text to display about waiver"""
        return f"""
### Waiver

{waiver['file']}: Line {waiver['row']}, waived on {waiver['date']}.

{waiver['type']}: {waiver['text']}

Waiving reason: {waiver['reason']}
"""

    def onLintSelectionUpdate(self, selected: QtCore.QItemSelection,
                              deselected: QtCore.QItemSelection):
        """Slot to display the details of the selected message or waiver"""
        del selected
        del deselected
        self.displayMessageDetails()

    def displayMessageDetails(self):
        """Based on the message/waiver selection, display details"""
        selection_model = self.message_table.selectionModel()
        if selection_model.hasSelection():
            message = selection_model.selection().indexes()[0].internalPointer(
            )

            if self.checkIfMessage(message):
                text = self.messageDetails(message)
                waiver = self.message_table.model().findWaiver(message)
                if waiver is not None:
                    text += self.waiverDetails(waiver)
            else:
                text = self.waiverDetails(message)
        else:
            text = ""

        self.text.setMarkdown(text)

    def onDiffUpdate(self, text: str = ""):
        """Slot to handle a change in the selected build to diff off of"""
        del text
        self.onUpdate()

    def loadMessages(self, prefix: str) -> Sequence[MessageListType]:
        """Loads messages and waivers with the given prefix"""
        waivers_path = self.config.build_path / f"{prefix}_waivers.yaml"
        if not waivers_path.exists():
            waivers_steal_path, ok = QtWidgets.QFileDialog.getOpenFileName(
                self.message_table,
                "Please select an existing waivers file or cancel to create an empty file.",
                str(self.config.build_path),
                f"Waiver files ({prefix}_waivers.yaml)")

            if ok:
                shutil.copy(waivers_steal_path, str(waivers_path))
            else:
                # create empty waivers file
                dump([], open(waivers_path, "w"))

        try:
            messages = safe_load(
                open(self.config.build_path / f"{prefix}_messages.yaml"))
            waivers = safe_load(open(waivers_path))
        except FileNotFoundError:
            # TODO this doesn't handle this error properly...
            self.log("Unable to load messages.")

        diff_build_path = self.config.builds_path / self.diff_tab.diff_choose.currentText(
        )
        diff_build_status = safe_load(
            open(diff_build_path / "build_status.yaml"))

        # Load diff builds conditionally
        diff_messages, diff_waivers = ([], [])
        if diff_build_status[self.status_name]:
            diff_messages = safe_load(
                open(diff_build_path / f"{prefix}_messages.yaml"))
            diff_waivers = safe_load(
                open(diff_build_path / f"{prefix}_waivers.yaml"))

        return (messages, waivers, diff_messages, diff_waivers)

    def updateDiffBuilds(self):
        """Updates the QComboBox where the build to diff against is selected"""
        listed_builds = list(
            self.diff_tab.diff_choose.itemText(i)
            for i in range(self.diff_tab.diff_choose.count()))
        for build in self.config.builds:
            if not build in listed_builds:
                self.diff_tab.diff_choose.addItem(build)
        self.diff_tab.diff_choose.update()

    def shouldLoadMessages(self) -> bool:
        """Determines if messages should be loaded from filesystem or not"""
        return self.config.status[self.status_name]

    def modelUpdate(self):
        """Slot for managing model updates"""
        model = self.messageModel([], [])
        diff_model = self.diffMessageModel([], [], [], [])
        # Hide unless we specifically have orphans
        self.message_show_orphans.hide()
        if self.config.build is not None:
            self.updateDiffBuilds()

            if self.shouldLoadMessages():
                try:
                    self.updateSummary()
                    (messages, waivers, diff_messages,
                     diff_waivers) = self.loadMessages(self.waiver_type)

                    model = self.messageModel(messages, waivers)
                    diff_model = self.diffMessageModel(messages, diff_messages,
                                                       waivers, diff_waivers)

                    model.view_full_filenames = self._view_full_filenames
                    diff_model.view_full_filenames = self._view_full_filenames

                    # We have orphans, we can show the orphans filter
                    if len(model.orphans.messages) > 0:
                        self.message_show_orphans.show()
                except FileNotFoundError:
                    self.log(
                        f"Error: unable to load {self.waiver_type} messages/waivers"
                    )

        self.message_table.setModel(model)
        self.diff_tab.table.setModel(diff_model)
        self.message_table.selectionModel().currentRowChanged.connect(
            self.onSelection)
        self.viewUpdate()

    def viewUpdate(self):
        """Slot for managing view updates"""
        self.filterLints()
        self.message_table.selectionModel().selectionChanged.connect(
            self.onLintSelectionUpdate)
        self.updateSummary()

    def updateSummary(self):
        """Updates summary text with generated summary"""
        self.summary_text.setMarkdown(self.generateSummary())

    def generateSummary(self) -> str:
        """Required to implement in subclass. Generates the summary text"""
        raise NotImplementedError

    def update(self):
        self.viewUpdate()
        self.modelUpdate()


#### Tabs for the "extra" functions


class DiffViewTab(QtWidgets.QWidget):
    """Tab to view the differences between messages in different builds"""
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)

        # Diff build selection
        self.diff_widget = QtWidgets.QWidget(self)
        self.diff_layout = QtWidgets.QHBoxLayout(self.diff_widget)
        self.diff_label = QtWidgets.QLabel(self.diff_widget)
        self.diff_label.setText("View differences between build")
        self.diff_label.setAlignment(QtCore.Qt.AlignRight
                                     | QtCore.Qt.AlignVCenter)
        self.diff_choose = QtWidgets.QComboBox(self.diff_widget)
        self.diff_choose.setObjectName("diff_choose")
        self.diff_layout.addWidget(self.diff_label, 2)
        self.diff_layout.addWidget(self.diff_choose, 2)

        # Differential view table
        self.table = QtWidgets.QTableView(self)
        self.table.setObjectName("diff_tab.table")
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        # TODO select appropriate column in left/right side based on other selection
        # (this will probably be a lot of work)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setHorizontalScrollMode(self.table.ScrollPerPixel)

        self.layout.addWidget(self.diff_widget)
        self.layout.addWidget(self.table)


class OrphanTab(QtWidgets.QWidget):
    """Orphan view tab. Allows for easier cleanup of orphaned waivers

    I guess this name is misleading, it doesn't show orphans, it shows messages
    that are in the same file as an orphan, and can be used to match orphans to
    current messages
    """

    # Signal to pass out information about the orphan to update
    orphanUpdate = QtCore.Signal(dict)
    # Open a file
    fileOpened = QtCore.Signal(str, int)

    def __init__(self, parent, config, messageModel: Messages):
        super().__init__(parent)

        self.config = config
        self.messageModel = messageModel

        self.layout = QtWidgets.QVBoxLayout(self)
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical, self)
        self.layout.addWidget(self.splitter)

        # Table setup
        self.table = QtWidgets.QTableView(self.splitter)
        self.table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Interactive)
        self.table.setHorizontalScrollMode(self.table.ScrollPerPixel)

        # Message info box
        self.message_info = QtWidgets.QTextEdit(self.splitter)
        self.message_info.setReadOnly(True)

        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.message_info)

        # Context menu
        self.update_orphan_act = QtWidgets.QAction("Update Orphan", self)
        self.update_orphan_act.triggered.connect(self.updateOrphan)
        self.open_file_act = QtWidgets.QAction("Open in editor", self)
        self.open_file_act.triggered.connect(self.openFile)
        self.context_menu = QtWidgets.QMenu(self)
        self.context_menu.addSection("Orphan Management")
        self.context_menu.addAction(self.update_orphan_act)
        self.context_menu.addAction(self.open_file_act)

    def modelUpdate(self, messages, filename: str = ""):
        """Updates the messages to be viewed based on the filename

        Should only be passed a list of unwaivered messages
        """
        # Don't bother with searching if we don't have a selection
        if filename == "":
            m = []
        else:
            m = [
                message for message in messages if message["file"] == filename
            ]
        self.table.setModel(self.messageModel(m, []))
        self.table.selectionModel().currentChanged.connect(
            self.updateMessageInfo)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        """Overridden to make a custom context menu in this widget"""
        selection_model = self.table.selectionModel()
        if selection_model is not None:
            if selection_model.hasSelection():
                self.context_menu.exec_(event.globalPos())

    def updateOrphan(self):
        """Updates the selected orphan with the selected message"""
        selection_model = self.table.selectionModel()
        if selection_model is not None:
            if selection_model.hasSelection():
                self.orphanUpdate.emit(
                    selection_model.currentIndex().internalPointer())
                self.modelUpdate([])

    def openFile(self):
        """Opens the line relevant to the selected message in a new editor tab"""
        selection_model = self.table.selectionModel()
        if selection_model is not None:
            if selection_model.hasSelection():
                message = selection_model.currentIndex().internalPointer()
                self.fileOpened.emit(message["file"], message["row"])

    def updateMessageInfo(self, current: QtCore.QModelIndex,
                          previous: QtCore.QModelIndex):
        """Updates message info box"""
        message = current.internalPointer()

        try:
            details = f"{message['type']}: {message['text']}"
        except KeyError:
            details = f"{message['text']}"

        text = f"""### Message Details

{details}
"""

        self.message_info.setMarkdown(text)
