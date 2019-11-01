from __future__ import annotations
from typing import List

import copy
import sys

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
import qdarkstyle

import chisurf.decorators
import chisurf.experiments.widgets
import chisurf.tools
import chisurf.fluorescence
import chisurf.experiments.data
import chisurf.settings
import chisurf.widgets
import chisurf.fluorescence.fcs
import chisurf.fio.widgets


settings = chisurf.settings.cs_settings['correlator']
plot_settings = chisurf.settings.gui['plot']
lw = plot_settings['line_width']


class Correlator(QtCore.QThread):

    procDone = QtCore.pyqtSignal(bool)
    partDone = QtCore.pyqtSignal(int)

    @property
    def data(
            self
    ) -> chisurf.experiments.data.DataCurve:
        if isinstance(
                self._data_curve,
                chisurf.experiments.data.DataCurve
        ):
            return self._data_curve
        else:
            return chisurf.experiments.data.DataCurve(
                setup=self
            )

    def __init__(
            self,
            photon_source,
            *args,
            **kwargs
    ):
        super().__init__(
            *args,
            **kwargs
        )
        self.p = photon_source
        self.exiting = False
        self._data_curve = None
        self._results = list()
        self._dt1 = 0
        self._dt2 = 0

    def getWeightStream(
            self,
            tacWeighting,
            max_number_of_routing_channels: int = 256
    ) -> np.ndarray:
        """
        :param tacWeighting: is either a list of integers or a numpy-array.
        If it's a list of integers the integers correspond to channel-numbers.
        In this case all photons have an equal weight of one. If tacWeighting
        is a numpy-array it should be of shape [max-routing, number of TAC
        channels]. The array contains np.floats with weights for photons
        arriving at different TAC-times.
        :return: numpy-array with same length as photon-stream, each photon
        is associated to one weight.
        """
        print("Correlator:getWeightStream")
        photons = self.p.photon_source.photons
        if type(tacWeighting) is list:
            print("channel-wise selection")
            #print("Max-Rout: %s" % photons.n_rout)
            wt = np.zeros(
                [max_number_of_routing_channels, photons.n_tac],
                dtype=np.float32
            )
            wt[tacWeighting] = 1.0
        elif type(tacWeighting) is np.ndarray:
            print("TAC-weighted")
            wt = tacWeighting
        w = chisurf.fluorescence.fcs.correlate.get_weights(
            photons.routing_channels,
            photons.micro_times,
            wt,
            photons.nPh
        )
        return w

    def run(self):
        data_curve = chisurf.experiments.data.DataCurve()

        w1 = self.getWeightStream(self.p.ch1)
        w2 = self.getWeightStream(self.p.ch2)
        print("Correlation running...")
        print("Correlation method: %s" % self.p.method)
        print("Fine-correlation: %s" % self.p.fine)
        print("Data stream split into %s correlations." % self.p.split)
        photons = self.p.photon_source.photons
        n_tac = photons.n_tac

        self._results = list()
        n_photons = len(photons)
        n_groups = self.p.split
        n_photons_per_groups = n_photons // n_groups
        dt = self.p.dt
        B = self.p.B
        self.partDone.emit(0.0)

        for i_group in range(n_groups):
            print("Correlation Nbr.: %s" % i_group)
            index_start = i_group * (n_photons_per_groups - 1)
            index_stop = (i_group + 1) * (n_photons_per_groups - 1)
            p = photons[index_start: index_stop]
            wi1 = w1[index_start: index_stop]
            wi2 = w2[index_start: index_stop]
            cr_filter = np.ones_like(wi1)
            if self.p.method == 'tp':
                results = chisurf.fluorescence.fcs.correlate.log_corr(
                    p.macro_times, p.micro_times, p.routing_channels, cr_filter,
                    wi1, wi2,
                    self.p.B, self.p.number_of_cascades,
                    self.p.fine,
                    n_tac
                )
                np_1 = results['number_of_photons_ch1']
                np_2 = results['number_of_photons_ch2']
                dt_1 = results['measurement_time_ch1']
                dt_2 = results['measurement_time_ch2']
                tau = results['correlation_time_axis']
                corr = results['correlation_amplitude']
                cr = chisurf.fluorescence.fcs.correlate.normalize(
                    np_1, np_2,
                    dt_1, dt_2,
                    tau, corr,
                    B
                )
                cr /= dt
                dur = float(min(dt_1, dt_2)) * self.p.dt / 1000.0  # seconds
                tau = tau.astype(np.float64)
                tau *= self.p.dt
                self._results.append([cr, dur, tau, corr])
            self.partDone.emit(float(i_group + 1) / n_groups * 100)

        # Calculate average correlations
        cors = list()
        taus = list()
        weights = list()
        for c in self._results:
            cr, dur, tau, corr = c
            weight = self.weight(tau, corr, dur, cr)
            weights.append(weight)
            cors.append(corr)
            taus.append(tau)

        cor = np.array(cors)
        w = np.array(weights)

        data_curve.x = np.array(taus).mean(axis=0)[1:]
        data_curve.y = cor.mean(axis=0)[1:]
        data_curve.ey = 1. / w.mean(axis=0)[1:]

        print("correlation done")
        self._data_curve = data_curve
        self.procDone.emit(True)
        self.exiting = True

    def weight(
            self,
            tau: np.ndarray,
            cor: np.ndarray,
            acquisition_time: float,
            count_rate: float
    ):
        """
        tau-axis in milliseconds
        correlation amplitude
        acquisition_time = duration in seconds
        count_rate = count-rate in kHz
        """
        if self.p.weighting == 1:
            return chisurf.fluorescence.fcs.weights(
                tau, cor, acquisition_time, count_rate, weight_type='uniform'
            )
        elif self.p.weighting == 0:
            return chisurf.fluorescence.fcs.weights(
                tau, cor, acquisition_time, count_rate, weight_type='suren'
            )


class CorrelatorWidget(QtWidgets.QWidget):

    @chisurf.decorators.init_with_ui(
        ui_filename="correlatorWidget.ui"
    )
    def __init__(
            self,
            photon_source,
            ch1: int = '0',
            ch2: int = '8',
            number_of_cascades: int = settings['number_of_cascades'],
            B: int = settings['B'],
            split: int = settings['split'],
            weighting: str = settings['weighting'],
            fine: bool = settings['fine']
    ):
        self.number_of_cascades = number_of_cascades
        self.B = B
        self.split = split
        self.weighting = weighting
        self.fine = fine
        self.cr = 0.0
        self.ch1 = ch1
        self.ch2 = ch2

        self.photon_source = photon_source
        self.correlator_thread = Correlator(
            photon_source=self
        )

        # fill widgets
        self.comboBox_3.addItems(chisurf.fluorescence.fcs.weightCalculations)
        self.comboBox_2.addItems(chisurf.fluorescence.fcs.correlationMethods)
        self.checkBox.setChecked(True)
        self.checkBox.setChecked(False)
        self.progressBar.setValue(0.0)

        # connect widgets
        self.pushButton_3.clicked.connect(self.correlator_thread.start)
        self.correlator_thread.partDone.connect(self.updateProgressBar)

    def updateProgressBar(self, val):
        self.progressBar.setValue(val)

    @property
    def data(
            self
    ) -> chisurf.experiments.data.DataCurve:
        return self.correlator_thread.data

    @property
    def dt(self):
        dt = self.photon_source.photons.mt_clk
        if self.fine:
            dt /= self.photon_source.photons.n_tac
        return dt

    @property
    def weighting(
            self
    ) -> int:
        return self.comboBox_3.currentIndex()

    @weighting.setter
    def weighting(
            self,
            v: int
    ):
        self.comboBox_3.setCurrentIndex(int(v))

    @property
    def ch1(
            self
    ) -> List[int]:
        return [int(x) for x in str(self.lineEdit_4.text()).split()]

    @ch1.setter
    def ch1(
            self,
            v: str
    ):
        self.lineEdit_4.setText(str(v))

    @property
    def ch2(
            self
    ) -> List[int]:
        return [int(x) for x in str(self.lineEdit_5.text()).split()]

    @ch2.setter
    def ch2(
            self,
            v: str
    ):
        self.lineEdit_5.setText(str(v))

    @property
    def fine(
            self
    ) -> int:
        return int(self.checkBox.isChecked())

    @fine.setter
    def fine(
            self,
            v: bool
    ):
        self.checkBox.setCheckState(v)

    @property
    def B(
            self
    ) -> int:
        return int(self.spinBox_3.value())

    @B.setter
    def B(
            self,
            v: int
    ):
        return self.spinBox_3.setValue(v)

    @property
    def number_of_cascades(
            self
    ) -> int:
        return int(self.spinBox_2.value())

    @number_of_cascades.setter
    def number_of_cascades(
            self,
            v: int
    ):
        return self.spinBox_2.setValue(v)

    @property
    def method(
            self
    ) -> str:
        return str(self.comboBox_2.currentText())

    @property
    def split(
            self
    ) -> float:
        return int(self.spinBox.value())

    @split.setter
    def split(
            self,
            v: float
    ):
        self.spinBox.setValue(v)


class CrFilterWidget(QtWidgets.QWidget):

    @chisurf.decorators.init_with_ui(
        ui_filename='fcs-cr-filter.ui'
    )
    def __init__(
            self,
            photon_source,
            verbose: bool = chisurf.verbose,
            time_window = settings['time_window'],
            max_count_rate = settings['max_count_rate'],
    ):
        self.photon_source = photon_source
        self.verbose = verbose
        self.time_window = time_window
        self.max_count_rate = max_count_rate
        self.sample_name = self.photon_source.sample_name

    @property
    def max_count_rate(self) -> float:
        return float(self.lineEdit_6.text())

    @max_count_rate.setter
    def max_count_rate(
            self,
            v: float
    ):
        self.lineEdit_6.setText(str(v))

    @property
    def time_window(self) -> float:
        return float(self.lineEdit_8.text())

    @time_window.setter
    def time_window(
            self,
            v: float
    ):
        self.lineEdit_8.setText(str(v))

    @property
    def cr_filter_on(self) -> bool:
        return bool(self.groupBox_2.isChecked())

    @property
    def photons(
            self
    ) -> chisurf.fio.photons.Photons:
        photons = self.photon_source.photons
        if self.cr_filter_on:
            dt = photons.mt_clk
            tw = int(self.time_window / dt)
            n_ph_max = int(self.max_count_rate * self.time_window)
            if self.verbose:
                print("Using count-rate filter:")
                print("Window-size [ms]: %s" % self.time_window)
                print("max_count_rate [kHz]: %s" % self.max_count_rate)
                print("n_ph_max in window [#]: %s" % n_ph_max)
                print("Window-size [n(MTCLK)]: %s" % tw)
                print("---------------------------------")

            mt = photons.macro_times
            n_ph = mt.shape[0]
            w = np.ones(n_ph, dtype=np.float32)
            chisurf.fluorescence.fcs.correlate.count_rate_filter(
                mt,
                tw,
                n_ph_max,
                w,
                n_ph
            )
            photons.cr_filter = w
            return photons
        else:
            return photons


class CorrelateTTTR(
    QtWidgets.QWidget
):

    name = "tttr-correlate"

    @property
    def curve_name(self):
        s = str(self.lineEdit.text())
        if len(s) == 0:
            return "no-name"
        else:
            return s

    def onRemoveDataset(self):
        selected_index = [
            i.row() for i in self.cs.selectedIndexes()
        ]
        l = list()
        for i, c in enumerate(self._curves):
            if i not in selected_index:
                l.append(c)
        self._curves = l
        self.cs.update()
        self.plot_curves()

    def clear_curves(self):
        self._curves = list()
        plot = self.plot.getPlotItem()
        plot.clear()

    def get_data_curves(self, **kwargs):
        return self._curves

    def plot_curves(self):
        self.legend.close()
        plot = self.plot.getPlotItem()
        plot.clear()

        self.legend = plot.addLegend()
        plot.setLogMode(x=True, y=False)
        plot.showGrid(True, True, 1.0)

        current_curve = self.cs.selected_curve_index
        for i, curve in enumerate(self._curves):
            l = lw * 0.5 if i != current_curve else 1.5 * lw
            plot.plot(
                x=curve.x, y=curve.y,
                pen=pg.mkPen(
                    chisurf.settings.colors[i % len(chisurf.settings.colors)]['hex'],
                    width=l
                ),
                name=curve.name
            )

    def add_curve(self):
        #d.setup = self
        #d.name = self.corr.fileWidget.sample_name
        self._curves.append(self.correlator.data)
        self.cs.update()
        self.plot_curves()

    @chisurf.decorators.init_with_ui(
        ui_filename="tttr_correlate.ui"
    )
    def __init__(self):
        self._curves = list()

        self.fileWidget = chisurf.fio.widgets.SpcFileWidget()
        self.verticalLayout.addWidget(self.fileWidget)

        self.countrateFilterWidget = CrFilterWidget(
            photon_source=self.fileWidget
        )
        self.verticalLayout_4.addWidget(self.countrateFilterWidget)

        self.correlator = CorrelatorWidget(
            photon_source=self.countrateFilterWidget
        )
        self.verticalLayout.addWidget(self.correlator)

        self.cs = chisurf.experiments.widgets.ExperimentalDataSelector(
            get_data_sets=self.get_data_curves,
            click_close=False
        )
        self.verticalLayout_6.addWidget(self.cs)

        self.correlator.correlator_thread.finished.connect(self.add_curve)
        #self.curve_selector.itemClicked[QListWidgetItem].connect(self.plot_curves)

        self.plot = pg.PlotWidget()
        plot = self.plot.getPlotItem()
        self.verticalLayout_9.addWidget(self.plot)
        self.legend = plot.addLegend()
        self.cs.onRemoveDataset = self.onRemoveDataset


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = CorrelateTTTR()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    win.show()
    sys.exit(app.exec_())
