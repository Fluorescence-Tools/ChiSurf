from __future__ import annotations

import numpy as np

import mfm
import mfm.cmd
import mfm.fluorescence.tcspc.convolve
import mfm.fluorescence.tcspc.corrections
import mfm.math
import mfm.fluorescence
from mfm.curve import Curve
from mfm.fitting.parameter import FittingParameterGroup, FittingParameter


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
    def t_bg(self) -> float:
        """Measurement time of background-measurement
        """
        return self._tmeas_bg.value

    @t_bg.setter
    def t_bg(
            self,
            v: float
    ):
        self._tmeas_bg.value = v

    @property
    def t_exp(self) -> float:
        """Measurement time of experiment
        """
        return self._tmeas_exp.value

    @t_exp.setter
    def t_exp(
            self,
            v: float
    ):
        self._tmeas_exp.value = v

    def __init__(
            self,
            background_curve: mfm.experiments.data.DataCurve = None,
            **kwargs
    ):
        kwargs['name'] = 'Nuisance'
        FittingParameterGroup.__init__(self, **kwargs)

        self._background_curve = background_curve
        self._sc = FittingParameter(value=0.0, name='sc', model=self.model)
        self._bg = FittingParameter(value=0.0, name='bg', model=self.model)
        self._tmeas_bg = FittingParameter(value=1.0, name='tBg', lb=0.001, ub=10000000, fixed=True)
        self._tmeas_exp = FittingParameter(value=1.0, name='tMeas', lb=0.001, ub=10000000, fixed=True)


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

    def calc_lintable(
            self,
            y,
            **kwargs
    ):
        window_function = kwargs.get('window_function', self.window_function)
        window_length = kwargs.get('window_length', self.window_length)
        xmin = kwargs.get('xmin', self.fit.xmin)
        xmax = kwargs.get('xmax', self.fit.xmax)
        return mfm.fluorescence.tcspc.corrections.compute_linearization_table(y, window_length, window_function, xmin, xmax)

    @property
    def measurement_time(self):
        return self.fit.model.generic.t_exp

    @measurement_time.setter
    def measurement_time(self, v):
        self.fit.model.generic.t_exp = v

    @property
    def rep_rate(self) -> float:
        return self.fit.model.convolve.rep_rate

    @rep_rate.setter
    def rep_rate(
            self,
            v: float
    ):
        self.fit.model.convolve.rep_rate = v

    @property
    def dead_time(self) -> float:
        return self._dead_time.value

    @dead_time.setter
    def dead_time(
            self,
            v: float
    ):
        self._dead_time.value = v

    def pileup(
            self,
            decay: np.array,
            **kwargs
    ):
        data = kwargs.get('data', self.fit.data.y)
        rep_rate = kwargs.get('rep_rate', self.rep_rate)
        dead_time = kwargs.get('dead_time', self.dead_time)
        meas_time = kwargs.get('meas_time', self.measurement_time)
        if self.correct_pile_up:
            mfm.fluorescence.tcspc.corrections.correct_model_for_pile_up(data, decay, rep_rate, dead_time, meas_time, verbose=self.verbose)

    def linearize(
            self,
            decay: np.array,
            **kwargs
    ):
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


class Convolve(FittingParameterGroup):

    @property
    def dt(self):
        return self._dt.value

    @dt.setter
    def dt(self, v):
        self._dt.value = v

    @property
    def lamp_background(self):
        return self._lb.value / self.n_photons_irf

    @lamp_background.setter
    def lamp_background(self, v):
        self._lb.value = v

    @property
    def timeshift(self):
        return self._ts.value

    @timeshift.setter
    def timeshift(self, v):
        self._ts.value = v

    @property
    def start(self):
        return int(self._start.value / self.dt)

    @start.setter
    def start(self, v):
        self._start.value = v

    @property
    def stop(self):
        stop = int(self._stop.value / self.dt)
        return stop

    @stop.setter
    def stop(self, v):
        self._stop.value = v

    @property
    def rep_rate(self):
        return self._rep.value

    @rep_rate.setter
    def rep_rate(self, v):
        self._rep.value = float(v)

    @property
    def do_convolution(self) -> bool:
        return self._do_convolution

    @do_convolution.setter
    def do_convolution(
            self,
            v: bool
    ):
        self._do_convolution = bool(v)

    @property
    def n0(self) -> float:
        return self._n0.value

    @n0.setter
    def n0(self, v: float):
        self._n0.value = v

    @property
    def irf(self) -> mfm.curve.Curve:
        irf = self._irf
        if isinstance(irf, Curve):
            irf = self._irf
            irf = (irf - self.lamp_background) << self.timeshift
            irf.y = np.maximum(irf.y, 0)
            return irf
        else:
            x = np.copy(self.data.x)
            y = np.zeros_like(self.data.y)
            y[0] = 1.0
            curve = mfm.curve.Curve(x=x, y=y)
            return curve

    @property
    def _irf(self):
        return self.__irf

    @_irf.setter
    def _irf(
            self,
            v: mfm.curve.Curve
    ):
        self.n_photons_irf = v.normalize(mode="sum")
        self.__irf = v
        try:
            # Approximate n0 the initial number of donor molecules in the
            # excited state
            data = self.data
            # Detect in which channel IRF starts
            x_irf = np.argmax(v.y > 0.005)
            x_min = data.x[x_irf]
            # Shift the time-axis by the number of channels
            x = data.x[x_irf:] - x_min
            y = data.y[x_irf:]
            # Using the average arrival time estimate the initial
            # number of molecules in the excited state
            tau0 = np.dot(x, y).sum() / y.sum()
            self.n0 = y.sum() / tau0
        except AttributeError:
            self.n0 = 1000.

    @property
    def data(self) -> mfm.experiments.data.DataCurve:
        if self._data is None:
            try:
                return self.fit.data
            except AttributeError:
                return None
        else:
            return self._data

    @data.setter
    def data(
            self,
            v: mfm.experiments.data.DataCurve
    ):
        self._data = v

    def scale(
            self,
            decay: mfm.experiments.data.DataCurve,
            **kwargs
    ):
        start = kwargs.get('start', min(0, self.start))
        stop = kwargs.get('stop', min(self.stop, len(decay)))
        bg = kwargs.get('bg', 0.0)
        autoscale = kwargs.get('autoscale', self._n0.fixed)
        data = kwargs.get('data', self.data)

        if autoscale:
            weights = 1./data.ey
            self.n0 = float(mfm.fluorescence.tcspc.rescale_w_bg(decay, data.y, weights, bg, start, stop))
        else:
            decay *= self.n0

        return decay

    def convolve(
            self,
            data: mfm.experiments.data.DataCurve,
            **kwargs
    ):
        verbose = kwargs.get('verbose', mfm.verbose)
        mode = kwargs.get('mode', self.mode)
        dt = kwargs.get('dt', self.dt)
        rep_rate = kwargs.get('rep_rate', self.rep_rate)
        irf = kwargs.get('irf', self.irf)
        scatter = kwargs.get('scatter', 0.0)
        decay = kwargs.get('decay', np.zeros(self.data.y.shape))

        # Make sure used IRF is of same size as data-array
        irf_y = np.resize(irf.y, self.data.y.shape)
        n_points = irf_y.shape[0]
        stop = min(self.stop, n_points)
        start = min(0, self.start)

        if mode == "per":
            period = 1000. / rep_rate
            mfm.fluorescence.tcspc.convolve.fconv_per_cs(decay, data, irf_y, start, stop, n_points, period, dt, n_points)
            # TODO: in future non linear time-axis (better suited for exponentially decaying data)
            # time = fit.data._x
            # mfm.fluorescence.tcspc.fconv_per_dt(decay, lifetime_spectrum, irf_y, start, stop, n_points, period, time)
        elif mode == "exp":
            t = self.data.x
            mfm.fluorescence.tcspc.convolve.fconv(decay, data, irf_y, stop, t)
        elif mode == "full":
            decay = np.convolve(data, irf_y, mode="full")[:n_points]

        if verbose:
            print("------------")
            print("Convolution:")
            print("Lifetimes: %s" % data)
            print("dt: %s" % dt)
            print("Irf: %s" % irf.name)
            print("Stop: %s" % stop)
            print("dt: %s" % dt)
            print("Convolution mode: %s" % mode)

        decay += (scatter * irf_y)

        return decay

    def __init__(
            self,
            fit: mfm.fitting.fit.Fit,
            **kwargs
    ):
        kwargs['name'] = 'Convolution'
        kwargs['fit'] = fit
        super(Convolve, self).__init__(**kwargs)

        self._data = None
        try:
            data = kwargs.get('data', fit.data)
            dt = data.dt[0]
            rep_rate = data.setup.rep_rate
            stop = len(data) * dt
            self.data = data
        except AttributeError:
            dt = kwargs.get('dt', 1.0)
            rep_rate = kwargs.get('rep_rate', 1.0)
            stop = 1
            data = kwargs.get('data', None)
        self.data = data

        self._n0 = FittingParameter(value=mfm.settings.cs_settings['tcspc']['n0'],
                                    name='n0',
                                    fixed=mfm.settings.cs_settings['tcspc']['autoscale'],
                                    decimals=2)
        self._dt = FittingParameter(value=dt, name='dt', fixed=True, digits=4)
        self._rep = FittingParameter(value=rep_rate, name='rep', fixed=True)
        self._start = FittingParameter(value=0.0, name='start', fixed=True)
        self._stop = FittingParameter(value=stop, name='stop', fixed=True)
        self._lb = FittingParameter(value=0.0, name='lb')
        self._ts = FittingParameter(value=0.0, name='ts')
        self._do_convolution = mfm.settings.cs_settings['tcspc']['convolution_on_by_default']
        self.mode = mfm.settings.cs_settings['tcspc']['default_convolution_mode']
        self.n_photons_irf = 1.0
        self.__irf = kwargs.get('irf', None)
        if self.__irf is not None:
            self._irf = self.__irf

