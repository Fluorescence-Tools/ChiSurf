from __future__ import annotations

import os.path
from typing import List
import numpy as np

from mfm.base import Data, Base
from mfm.curve import Curve
import mfm.experiments.experiment


class ExperimentalData(Data):

    def __init__(self, *args, **kwargs):
        super(ExperimentalData, self).__init__(*args, **kwargs)
        self.setup = kwargs.get('setup', None)
        self._experiment = kwargs.get('experiment', None)

    @property
    def experiment(self) -> mfm.experiments.experiment.Experiment:
        if self._experiment is None:
            if self.setup is None:
                return None
            else:
                return self.setup.experiment
        else:
            return self._experiment

    @experiment.setter
    def experiment(
            self,
            v: mfm.experiments.experiment.Experiment
    ):
        self._experiment = v

    def to_dict(self):
        d = Data.to_dict(self)
        d['setup'] = self.setup.to_dict()
        return d


class DataCurve(Curve, ExperimentalData):

    def __init__(self, *args, **kwargs):
        try:
            ex, ey = args[2], args[3]
        except IndexError:
            ex = kwargs.get('ex', np.ones_like(kwargs.get('x', None)))
            ey = kwargs.get('ey', np.ones_like(kwargs.get('y', None)))
        kwargs['ex'] = ex
        kwargs['ey'] = ey
        super(DataCurve, self).__init__(*args, **kwargs)
        filename = kwargs.pop('filename', '')

        if os.path.isfile(filename):
            self.load(filename, **kwargs)

    def __str__(self):
        s = "Dataset:\n"
        try:
            s += "filename: " + self.filename + "\n"
            s += "length  : %s\n" % len(self)
            s += "x\ty\terror-x\terror-y\n"

            lx = self.x[:3]
            ly = self.y[:3]
            lex = self.ex[:3]
            ley = self.ey[:3]

            ux = self.x[-3:]
            uy = self.y[-3:]
            uex = self.ex[-3:]
            uey = self.ey[-3:]

            for i in range(2):
                x, y, ex, ey = lx[i], ly[i], lex[i], ley[i]
                s += "{0:<12.3e}\t".format(x)
                s += "{0:<12.3e}\t".format(y)
                s += "{0:<12.3e}\t".format(ex)
                s += "{0:<12.3e}\t".format(ey)
                s += "\n"
            s += "....\n"
            for i in range(1):
                x, y, ex, ey = ux[i], uy[i], uex[i], uey[i]
                s += "{0:<12.3e}\t".format(x)
                s += "{0:<12.3e}\t".format(y)
                s += "{0:<12.3e}\t".format(ex)
                s += "{0:<12.3e}\t".format(ey)
                s += "\n"
        except:
            s += "This cuve does not 'own' data..."
        return s

    def to_dict(self) -> dict:
        d = Curve.to_dict(self)
        d.update(ExperimentalData.to_dict(self))
        d['ex'] = list(self.ex)
        d['ey'] = list(self.ey)
        d['weights'] = list(self.weights)
        d['experiment'] = self.experiment.to_dict()
        return d

    def from_dict(
            self,
            v: dict
    ):
        Curve.from_dict(self, v)
        self._kw['ex'] = np.array(v['ex'], dtype=np.float64)
        self._kw['ey'] = np.array(v['ey'], dtype=np.float64)

    def save(
            self,
            filename: str = None,
            mode: str = 'json'
    ):
        if filename is None:
            filename = os.path.join(self.name + '_data.txt')
        if mode == 'txt':
            mfm.io.ascii.Csv().save(self, filename)
        else:
            with open(filename, 'w') as fp:
                fp.write(self.to_json())

    def load(
            self,
            filename: str,
            **kwargs
    ):
        mode = kwargs.get('mode', 'txt')
        skiprows = kwargs.get('skiprows', 9)

        if mode == 'txt':
            csv = mfm.io.ascii.Csv()
            csv.load(filename, skiprows=skiprows)
            self._kw['x'] = csv.data[0]
            self._kw['y'] = csv.data[1]
            self._kw['ey'] = csv.data[2]
            self._kw['ex'] = csv.data[3]

    def set_data(
            self,
            filename: str,
            x: np.array,
            y: np.array,
            **kwargs
    ):
        """test docs

        :param filename:
        :param x:
        :param y:
        :param kwargs:
        :return:
        """
        self._kw['ex'] = kwargs.get('ex', np.zeros_like(x))
        self._kw['ey'] = kwargs.get('ey', np.ones_like(y))
        self.filename = filename
        self._kw['x'] = x
        self._kw['y'] = y

    def set_weights(
            self,
            w: np.array
    ):
        self._kw['weights'] = w

    def __getitem__(
            self,
            key: str
    ):
        x, y = Curve.__getitem__(self, key)
        return x, y, self.ey[key]

    @property
    def dt(self) -> np.array:
        """
        The derivative of the x-axis
        """
        return np.diff(self.x)


class DataGroup(list, Base):

    @property
    def names(self) -> List[str]:
        return [d.name for d in self]

    @property
    def current_dataset(self):
        return self[self._current_dataset]

    @current_dataset.setter
    def current_dataset(self, i):
        self._current_dataset = i

    @property
    def name(self) -> str:
        try:
            return self._kw['name']
        except KeyError:
            return self.names[0]

    @name.setter
    def name(
            self,
            v: str
    ):
        self._name = v

    def append(
            self,
            dataset: Data
    ):
        if isinstance(dataset, ExperimentalData):
            list.append(self, dataset)
        if isinstance(dataset, list):
            for d in dataset:
                if isinstance(d, ExperimentalData):
                    list.append(self, d)

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], list):
            list.__init__(self, args[0])
        else:
            list.__init__(self, [args[0]])
        Base.__init__(self, *args[1:], **kwargs)
        self._current_dataset = 0


class DataCurveGroup(DataGroup):

    @property
    def x(self) -> np.array:
        return self.current_dataset.x

    @x.setter
    def x(self,
          v: np.array):
        self.current_dataset.x = v

    @property
    def y(self) -> np.array:
        return self.current_dataset.y

    @y.setter
    def y(self,
          v: np.array):
        self.current_dataset.y = v

    @property
    def ex(self) -> np.array:
        return self.current_dataset.ex

    @ex.setter
    def ex(self,
           v: np.array):
        self.current_dataset.ex = v

    @property
    def ey(self) -> np.array:
        return self.current_dataset.ey

    @ey.setter
    def ey(self,
           v: np.array):
        self.current_dataset.ey = v

    def __str__(self):
        return [str(d) + "\n------\n" for d in self]

    def __init__(self, *args, **kwargs):
        DataGroup.__init__(self, *args, **kwargs)


class ExperimentDataGroup(DataGroup):

    @property
    def setup(self):
        return self[0].setup

    @setup.setter
    def setup(self, v):
        pass

    @property
    def experiment(self):
        return self.setup.experiment

    @experiment.setter
    def experiment(self, v):
        pass

    def __init__(self, *args, **kwargs):
        DataGroup.__init__(self, *args, **kwargs)


class ExperimentDataCurveGroup(ExperimentDataGroup, DataCurveGroup):

    @property
    def setup(self):
        return self[0].setup

    @setup.setter
    def setup(self, v):
        pass

    def __init__(self, *args, **kwargs):
        ExperimentDataGroup.__init__(self, *args, **kwargs)
        DataCurveGroup.__init__(self, *args, **kwargs)