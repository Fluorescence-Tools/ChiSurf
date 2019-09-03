from __future__ import annotations

from PyQt5 import QtWidgets

import mfm
import mfm.structure.widgets
from mfm.experiments.reader import ExperimentReader
from mfm.io.widgets import PDBLoad


class LoadStructure(QtWidgets.QWidget, ExperimentReader):

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self)
        ExperimentReader.__init__(self, *args, **kwargs)

        layout = QtWidgets.QVBoxLayout(self)
        self.layout = layout
        self.pdbWidget = PDBLoad(self)
        self.layout.addWidget(self.pdbWidget)

    def read(self, filename=None, **kwargs):
        self.pdbWidget.load(filename=filename)
        s = self.pdbWidget.structure
        s.setup = self
        return [s]

    def autofitrange(self, fit):
        return None, None


class LoadStructureFolder(QtWidgets.QWidget, ExperimentReader):

    name = 'Trajectory'

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self)
        ExperimentReader.__init__(self, *args, **kwargs)
        self.parent = kwargs.get('parent', None)

        layout = QtWidgets.QVBoxLayout(self)
        self.layout = layout
        self.pdbWidget = mfm.structure.widgets.PDBFolderLoad(self)
        self.layout.addWidget(self.pdbWidget)

    def read(self):
        return [self.pdbWidget.trajectory]

    def __str__(self):
        s = 'ProteinMC\n'
        return s

    def autofitrange(self, fit):
        return None, None

