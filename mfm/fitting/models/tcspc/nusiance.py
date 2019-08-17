import numpy as np
from PyQt5 import QtCore, QtWidgets, uic

import mfm
from mfm.curve import Curve
from mfm.parameter import FittingParameterGroup, FittingParameter
from mfm.widgets import CurveSelector

__author__ = 'Thomas'


class Generic(FittingParameterGroup):

    @property
    def n_ph_bg(self):
        """Number of background photons
        """
        if isinstance(self.background_curve, Curve):
            return self._background_curve.y.sum() / self.t_bg * self.t_exp
        else:
            return 0

    @property
    def n_ph_exp(self):
        """Number of experimental photons
        """
        if isinstance(self.fit.data, Curve):
            return self.fit.data.y.sum()
        else:
            return 0

    @property
    def n_ph_fl(self):
        """Number of fluorescence photons
        """
        return self.n_ph_exp - self.n_ph_bg

    @property
    def scatter(self):
        # Scatter amplitude
        return self._sc.value

    @scatter.setter
    def scatter(self, v):
        self._sc.value = v

    @property
    def background(self):
        # Constant background in fluorescence decay curve
        return self._bg.value

    @background.setter
    def background(self, v):
        self._bg.value = v

    @property
    def background_curve(self):
        # Background curve
        if isinstance(self._background_curve, Curve):
            return self._background_curve
        else:
            return None

    @background_curve.setter
    def background_curve(self, v):
        if isinstance(v, Curve):
            self._background_curve = v

    @property
    def t_bg(self):
        """Measurement time of background-measurement
        """
        return self._tmeas_bg.value

    @t_bg.setter
    def t_bg(self, v):
        self._tmeas_bg.value = v

    @property
    def t_exp(self):
        """Measurement time of experiment
        """
        return self._tmeas_exp.value

    @t_exp.setter
    def t_exp(self, v):
        self._tmeas_exp.value = v

    def __init__(self, **kwargs):
        kwargs['name'] = 'Nuisance'
        FittingParameterGroup.__init__(self, **kwargs)

        self._background_curve = None
        self._sc = FittingParameter(value=0.0, name='sc', model=self.model)
        self._bg = FittingParameter(value=0.0, name='bg', model=self.model)
        self._tmeas_bg = FittingParameter(value=1.0, name='tBg', lb=0.001, ub=10000000, fixed=True)
        self._tmeas_exp = FittingParameter(value=1.0, name='tMeas', lb=0.001, ub=10000000, fixed=True)

        self.background_curve = kwargs.get('background_curve', None)


class GenericWidget(Generic, QtWidgets.QWidget):

    def change_bg_curve(self, background_index=None):
        if isinstance(background_index, int):
            self.background_select.selected_curve_index = background_index
        self._background_curve = self.background_select.selected_dataset

        self.lineEdit.setText(self.background_select.curve_name)
        self.fit.model.update()

    def update_widget(self):
        self.lineedit_nphBg.setText("%i" % self.n_ph_bg)
        self.lineedit_nphFl.setText("%i" % self.n_ph_fl)

    def __init__(self, **kwargs):
        Generic.__init__(self, **kwargs)
        QtWidgets.QWidget.__init__(self)

        self.parent = kwargs.get('parent', None)
        if kwargs.get('hide_generic', False):
            self.hide()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        gb = QtWidgets.QGroupBox()
        gb.setTitle("Generic")
        self.layout.addWidget(gb)

        gbl = QtWidgets.QVBoxLayout()
        gbl.setSpacing(0)
        gbl.setContentsMargins(0, 0, 0, 0)

        gb.setLayout(gbl)
        # Generic parameters
        l = QtWidgets.QGridLayout()
        l.setSpacing(0)
        l.setContentsMargins(0, 0, 0, 0)
        gbl.addLayout(l)

        sc_w = self._sc.make_widget(update_function=self.update_widget, text='Sc')
        bg_w = self._bg.make_widget(update_function=self.update_widget, text='Bg')
        tmeas_bg_w = self._tmeas_bg.make_widget(update_function=self.update_widget, text='t<sub>Bg</sub>')
        tmeas_exp_w = self._tmeas_exp.make_widget(update_function=self.update_widget, text='t<sub>Meas</sub>')

        l.addWidget(sc_w, 1, 0)
        l.addWidget(bg_w, 1, 1)
        l.addWidget(tmeas_bg_w, 2, 0)
        l.addWidget(tmeas_exp_w, 2, 1)

        ly = QtWidgets.QHBoxLayout()
        l.addLayout(ly, 0, 0, 1, 2)
        ly.addWidget(QtWidgets.QLabel('Background file:'))
        self.lineEdit = QtWidgets.QLineEdit()
        ly.addWidget(self.lineEdit)

        open_bg = QtWidgets.QPushButton()
        open_bg.setText('...')
        ly.addWidget(open_bg)

        self.background_select = CurveSelector(parent=None, change_event=self.change_bg_curve, fit=self.fit)
        open_bg.clicked.connect(self.background_select.show)

        a = QtWidgets.QHBoxLayout()
        a.addWidget(QtWidgets.QLabel('nPh(Bg)'))
        self.lineedit_nphBg = QtWidgets.QLineEdit()
        a.addWidget(self.lineedit_nphBg)
        l.addLayout(a, 3, 0, 1, 1)

        a = QtWidgets.QHBoxLayout()
        a.addWidget(QtWidgets.QLabel('nPh(Fl)'))
        self.lineedit_nphFl = QtWidgets.QLineEdit()
        a.addWidget(self.lineedit_nphFl)
        l.addLayout(a, 3, 1, 1, 1)


class Corrections(FittingParameterGroup):

    @property
    def lintable(self):
        if self._lintable is None:
            self._lintable = np.ones_like(self.fit.data.y)
        return self._lintable[::-1] if self.reverse else self._lintable

    @lintable.setter
    def lintable(self, v):
        self._curve = v
        self._lintable = self.calc_lintable(v.y)

    @property
    def window_length(self):
        return int(self._window_length.value)

    @window_length.setter
    def window_length(self, v):
        self._window_length.value = v
        self._lintable = self.calc_lintable(self._curve.y)

    @property
    def window_function(self):
        return self._window_function

    @window_function.setter
    def window_function(self, v):
        self._window_function = v
        self._lintable = self.calc_lintable(self._curve.y)

    @property
    def reverse(self):
        return self._reverse

    @reverse.setter
    def reverse(self, v):
        self._reverse = v

    def calc_lintable(self, y, **kwargs):
        window_function = kwargs.get('window_function', self.window_function)
        window_length = kwargs.get('window_length', self.window_length)
        xmin = kwargs.get('xmin', self.fit.xmin)
        xmax = kwargs.get('xmax', self.fit.xmax)
        return mfm.fluorescence.tcspc.dnl_table(y, window_length, window_function, xmin, xmax)

    @property
    def measurement_time(self):
        return self.fit.model.generic.t_exp

    @measurement_time.setter
    def measurement_time(self, v):
        self.fit.model.generic.t_exp = v

    @property
    def rep_rate(self):
        return self.fit.model.convolve.rep_rate

    @rep_rate.setter
    def rep_rate(self, v):
        self.fit.model.convolve.rep_rate = v

    @property
    def dead_time(self):
        return self._dead_time.value

    @dead_time.setter
    def dead_time(self, v):
        self._dead_time.value = v

    def pileup(self, decay, **kwargs):
        data = kwargs.get('data', self.fit.data.y)
        rep_rate = kwargs.get('rep_rate', self.rep_rate)
        dead_time = kwargs.get('dead_time', self.dead_time)
        meas_time = kwargs.get('meas_time', self.measurement_time)
        if self.correct_pile_up:
            mfm.fluorescence.tcspc.pile_up(data, decay, rep_rate, dead_time, meas_time, verbose=self.verbose)

    def linearize(self, decay, **kwargs):
        lintable = kwargs.get('lintable', self.lintable)
        if lintable is not None and self.correct_dnl:
            return decay * lintable
        return decay

    def __init__(self, fit, **kwargs):
        kwargs['fit'] = fit
        kwargs['name'] = 'Corrections'
        FittingParameterGroup.__init__(self, **kwargs)

        self._lintable = None
        self._curve = None
        self._reverse = kwargs.get('reverse', False)
        self.correct_dnl = kwargs.get('correct_dnl', False)
        self._window_length = FittingParameter(value=17.0, name='win-size', fixed=True, decimals=0)
        self._window_function = kwargs.get('window_function', 'hanning')
        self.correct_pile_up = kwargs.get('correct_pile_up', False)

        self._auto_range = kwargs.get('lin_auto_range', True)
        self._dead_time = FittingParameter(value=85.0, name='tDead', fixed=True, decimals=1)


class CorrectionsWidget(Corrections, QtWidgets.QWidget):

    def __init__(self, fit, **kwargs):
        super(CorrectionsWidget, self).__init__(fit=fit, threshold=0.9, reverse=False, enabled=False)
        QtWidgets.QWidget.__init__(self)
        uic.loadUi("mfm/ui/fitting/models/tcspc/tcspcCorrections.ui", self)
        self.groupBox.setChecked(False)
        self.comboBox.addItems(mfm.math.signal.windowTypes)
        if kwargs.get('hide_corrections', False):
            self.hide()

        self._dead_time.make_widget(layout=self.horizontalLayout_2, text='t<sub>dead</sub>[ns]')
        self._window_length.make_widget(layout=self.horizontalLayout_2)

        self.lin_select = CurveSelector(parent=None,
                                        change_event=self.onChangeLin,
                                        fit=self.fit,
                                        setup=mfm.experiments.tcspc.TCSPCReader)

        self.actionSelect_lintable.triggered.connect(self.lin_select.show)

        self.checkBox_3.toggled.connect(lambda: mfm.run(
            "cs.current_fit.model.corrections.correct_pile_up = %s\n" % self.checkBox_3.isChecked())
        )

        self.checkBox_2.toggled.connect(lambda: mfm.run(
            "cs.current_fit.model.corrections.reverse = %s" % self.checkBox_2.isChecked())
        )

        self.checkBox.toggled.connect(lambda: mfm.run(
            "cs.current_fit.model.corrections.correct_dnl = %s" % self.checkBox.isChecked())
        )

        self.comboBox.currentIndexChanged.connect(lambda: mfm.run(
            "cs.current_fit.model.corrections.window_function = '%s'" % self.comboBox.currentText())
        )

    def onChangeLin(self):
        idx = self.lin_select.selected_curve_index
        t = "lin_table = cs.current_fit.model.corrections.lin_select.datasets[%s]\n" \
            "for f in cs.current_fit[cs.current_fit._selected_fit:]:\n" \
            "   f.model.corrections.lintable = mfm.curve.DataCurve(x=lin_table.x, y=lin_table.y)\n" \
            "   f.model.corrections.correct_dnl = True\n" % idx
        mfm.run(t)

        lin_name = self.lin_select.curve_name
        t = "for f in cs.current_fit[cs.current_fit._selected_fit:]:\n" \
            "   f.model.corrections.lineEdit.setText('%s')\n" \
            "   f.model.corrections.checkBox.setChecked(True)\n" % lin_name
        mfm.run(t)

        mfm.run("cs.current_fit.update()")
