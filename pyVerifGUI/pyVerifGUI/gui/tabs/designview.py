"""Class definition to handle the Design tab.
"""

__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from qtpy import QtWidgets, QtCore, QtGui
from yaml import full_load

from pyVerifGUI.tasks import task_names
from pyVerifGUI.gui.models import ModuleTreeItem, ModuleTreeItemModel


class DesignViewTab(QtWidgets.QWidget):
    """Allows visualisation of the design via module hierarchy"""

    log_output = QtCore.Signal(str)

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # Basic layout
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.setObjectName("layout")
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal,
                                            self)
        self.textBrowser = QtWidgets.QTextBrowser(self)
        self.textBrowser.setObjectName("textBrowser")
        self.label = QtWidgets.QLabel("Module Information", self)
        self.label.setObjectName("label")

        # Design hierarchy
        self.treeView = QtWidgets.QTreeView(self)
        self.treeView.setObjectName("treeView")
        self.treeView.setSelectionBehavior(self.treeView.SelectItems)
        self.treeView.setSelectionMode(self.treeView.SingleSelection)

        # Design info layout
        self.info_widget = QtWidgets.QWidget(self.splitter)
        self.info_layout = QtWidgets.QVBoxLayout(self.info_widget)
        self.info_layout.addWidget(self.label)
        self.info_layout.addWidget(self.textBrowser)

        # Layout organization
        self.splitter.addWidget(self.treeView)
        self.splitter.addWidget(self.info_widget)
        self.layout.addWidget(self.splitter)

        # Context menu
        self.copy_path_act = QtWidgets.QAction("Copy Hierarchical Path", self)
        self.copy_path_act.triggered.connect(self.copyHierarchy)
        self.copy_path_act.setShortcut(QtGui.QKeySequence("Ctrl+H"))
        self.context_menu = QtWidgets.QMenu(self)
        self.context_menu.addSection("Module")
        self.context_menu.addAction(self.copy_path_act)

        self.addAction(self.copy_path_act)

        self.sv_files = None
        self.sv_hierarchy = None
        self.sv_interfaces = None
        self.sv_modules = None

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent):
        """Overridden to generate a context menu"""
        selection_model = self.treeView.selectionModel()
        if selection_model is not None:
            self.context_menu.exec_(event.globalPos())

    def copyHierarchy(self):
        """Adds hierarchical path of currently selected module to clipboard"""
        selection_model = self.treeView.selectionModel()
        if selection_model is not None:
            if selection_model.hasSelection():
                module = selection_model.currentIndex()
                path = self.getHierarchy(module)
                QtWidgets.QApplication.clipboard().setText(path)
                self.log_output.emit(
                    f"Copied hierarchal path {path} to clipboard")

    def onUpdate(self):
        """Handles updating model or view"""
        if self.config.build is not None:
            if self.config.status[task_names.parse]:
                self.updateTree()
            else:
                self.removeTree()
                self.textBrowser.setPlainText("Parsing not completed!")

    def updateTree(self):
        """Called when new parsed design information is available"""

        if self.read_parsed():
            tree = ModuleTreeItem(self.config.build)
            tree.build(self.sv_hierarchy[self.config.top_module]["tree"])
        else:
            tree = ModuleTreeItem("unknown")
            tree.build({"No parsed files found!": {}})

        self.treeView.setModel(ModuleTreeItemModel(tree))
        selection_model = self.treeView.selectionModel()
        selection_model.currentChanged.connect(self.updateInfo)

        if not selection_model.hasSelection():
            index = self.treeView.model().index(0, 0, QtCore.QModelIndex())
            selection_model.setCurrentIndex(
                index, QtCore.QItemSelectionModel.SelectionFlag.Select)

    def removeTree(self):
        """Slot for when there is no design loaded"""
        tree = ModuleTreeItem("blank")
        self.treeView.setModel(ModuleTreeItemModel(tree))
        self.textBrowser.setPlainText("")

    def updateInfo(self, current: QtCore.QItemSelection,
                   previous: QtCore.QItemSelection):
        """Slot to update the information display based on the currently selected module"""
        del previous
        self.textBrowser.setPlainText(self.getModuleText(current))

    def getHierarchy(self, model: ModuleTreeItemModel) -> str:
        """Recursive function to find the hierarchical location of a certain item"""
        parent = model.parent()
        if parent != QtCore.QModelIndex():
            return (self.getHierarchy(parent) +
                    "." + model.internalPointer().name)

        return model.internalPointer().name

    def prettyPrintModule(self, model: QtCore.QModelIndex) -> str:
        """Prints the information about a module in a nice way"""

        module = self.sv_modules[model.internalPointer().name]
        text = f"{module['name']}: {module['path']}\n\n"

        path = self.getHierarchy(model)
        text += "Hierarchical Path: " + path + "\n\n"

        text += "Input ports:\n"
        for signal in module['ports']:
            if signal[0] == "input":
                text += f"  {signal[4]} {signal[3]}\n"
        text += "\n"

        text += "Output ports:\n"
        for signal in module['ports']:
            if signal[0] == "output":
                text += f"  {signal[4]} {signal[3]}\n"
        text += "\n"

        text += "Modules:\n"
        for submodule in module['submodules'].keys():
            text += f"  {submodule}"

        return text

    def getModuleText(self, model: QtCore.QModelIndex) -> str:
        """Gets the text to display in the module info box"""
        try:
            for key in self.sv_modules.keys():
                if key == model.internalPointer().name:
                    return self.prettyPrintModule(model)
        except AttributeError:
            return "Design has not been parsed!"

        return "Module not found!"

    def read_parsed(self) -> bool:
        """Read in YAML from parser

        Returns True if read succeeds
        """
        sv_parsed = f"sv_{self.config.top_module}"
        try:
            self.sv_hierarchy = full_load(
                open(self.config.build_path / sv_parsed / "sv_hierarchy.yaml"))
            self.sv_files = full_load(
                open(self.config.build_path / sv_parsed / "sv_files.yaml"))
            self.sv_modules = full_load(
                open(self.config.build_path / sv_parsed / "sv_modules.yaml"))
            self.sv_interfaces = full_load(
                open(self.config.build_path / sv_parsed /
                     "sv_interfaces.yaml"))
            return True
        except FileNotFoundError:
            self.sv_hierarchy = None
            self.sv_files = None
            self.sv_modules = None
            self.sv_interfaces = None
            return False
