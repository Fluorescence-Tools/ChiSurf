from __future__ import annotations
from typing import Tuple

import numpy as np
import pyqtgraph as pg
from qtpy import QtWidgets
from pyqtgraph.dockarea import DockArea, Dock

import chisurf
import chisurf.settings
import chisurf.fitting
import chisurf.parameter
import chisurf.decorators
import chisurf.models
from chisurf.plots import plotbase

plot_settings = chisurf.settings.gui['plot']
colors = plot_settings['colors']
color_scheme = chisurf.settings.colors
lw = plot_settings['line_width']


class ParameterScanWidget(
    QtWidgets.QWidget
):

    @chisurf.decorators.init_with_ui(
        ui_filename="parameter_scan.ui"
    )
    def __init__(
            self,
            model: chisurf.models.Model = None,
            parent: QtWidgets.QWidget = None,
            *args,
            **kwargs
    ):

        self.model = model
        self.parent = parent

        self.actionScanParameter.triggered.connect(self.scan_parameter)
        self.actionParameterChanged.triggered.connect(self.onParameterChanged)
        self.actionUpdateParameterList.triggered.connect(self.update)

        self.update()

    def onParameterChanged(self):
        self.parent.update_all()

    def update(
            self
    ) -> None:
        super().update()
        self.comboBox.blockSignals(True)

        pn = self.model.parameter_names
        self.comboBox.clear()
        self.comboBox.addItems(pn)

        self.comboBox.blockSignals(False)
        self.model.update_plots()

    def scan_parameter(
            self
    ) -> None:
        p_min = float(self.doubleSpinBox.value())
        p_max = float(self.doubleSpinBox_2.value())
        _, name = self.selected_parameter
        v = self.model.parameter_dict[name].value
        v_min = (1. - p_min) * v
        v_max = (1. + p_max) * v
        n_steps = int(self.spinBox.value())
        chisurf.run(
            "cs.current_fit.model.parameters_all_dict['%s'].scan(cs.current_fit, scan_range=(%s, %s), n_steps=%s)" % (
                self.parameter.name,
                v_min,
                v_max,
                n_steps
            )
        )
        self.parent.update_all()

    @property
    def selected_parameter(
            self
    ) -> Tuple[int, str]:
        idx = self.comboBox.currentIndex()
        name = self.comboBox.currentText()
        return idx, str(name)

    @property
    def parameter(
            self
    ) -> chisurf.parameter.Parameter:
        idx, name = self.selected_parameter
        try:
            return self.model.parameters_all_dict[name]
        except AttributeError:
            return None


class ParameterScanPlot(
    plotbase.Plot
):

    name = "Parameter scan"

    def __init__(
            self,
            fit: chisurf.fitting.fit.FitGroup,
            *args,
            **kwargs
    ):
        super(ParameterScanPlot, self).__init__(fit)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.data_x, self.data_y = None, None

        self.pltControl = ParameterScanWidget(
           model=fit.model,
           parent=self
        )

        area = DockArea()
        self.layout.addWidget(area)
        hide_title = plot_settings['hideTitle']
        d2 = Dock("Chi2-Surface", hideTitle=hide_title)

        self.p1 = QtWidgets.QPlainTextEdit()
        p2 = pg.PlotWidget()

        d2.addWidget(p2)

        area.addDock(d2, 'top')

        distribution_plot = p2.getPlotItem()

        self.distribution_plot = distribution_plot
        self.distribution_curve = distribution_plot.plot(
            x=[0.0],
            y=[0.0],
            pen=pg.mkPen(colors['data'], width=lw),
            name='Data'
        )

    def update_all(
            self,
            *args,
            **kwargs
    ) -> None:
        try:
            p = self.pltControl.parameter
            x, y = p.parameter_scan
            if isinstance(x, np.ndarray) and isinstance(y, np.ndarray):
                self.distribution_curve.setData(x=x, y=y)
        except:
            chisurf.logging.warning("ParameterScanPlot: update_all failed")

