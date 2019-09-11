from qtpy import  QtWidgets

import mfm
from mfm.plots import plotbase


class FitInfo(plotbase.Plot):

    name = "Info"

    def __init__(
            self,
            fit: mfm.fitting.fit.FitGroup,
            parent: QtWidgets.QWidget,
            **kwargs
    ):
        super(FitInfo, self).__init__(
            fit,
            parent=parent,
            **kwargs
        )
        self.pltControl = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self)
        self.textedit = QtWidgets.QPlainTextEdit()
        self.layout.addWidget(self.textedit)

    def update_all(
            self,
            *args,
            **kwargs
    ):
        fit = self.fit
        self.textedit.setPlainText(str(fit))


