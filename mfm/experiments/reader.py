"""

"""
from __future__ import annotations
from typing import Tuple, Callable, Dict

from abc import abstractmethod

import mfm.base
import mfm.curve
import mfm.experiments.data


class ExperimentReader(
    mfm.base.Base
):
    """

    """

    def __init__(
            self,
            experiment: mfm.experiments.experiment.Experiment,
            *args,
            controller: ExperimentReaderController = None,
            **kwargs
    ):
        """

        :param args:
        :param kwargs:
        """
        super().__init__(
            *args,
            **kwargs
        )
        self.experiment = experiment
        self._controller = controller

    @property
    def controller(
            self
    ) -> ExperimentReaderController:
        return self._controller

    @controller.setter
    def controller(
            self,
            v: ExperimentReaderController
    ):
        self._controller = v

    @staticmethod
    @abstractmethod
    def autofitrange(
            data: mfm.base.Data,
            **kwargs
    ) -> Tuple[int, int]:
        return 0, len(data.y) - 1

    @abstractmethod
    def read(
            self,
            name: str = None,
            *args,
            **kwargs
    ) -> mfm.base.Data:
        """

        :param name: A name that will be associated to the data set that is read.
        :param kwargs:
        :return:
        """
        pass

    def get_data(
            self,
            **kwargs
    ) -> mfm.experiments.data.ExperimentDataGroup:
        data = self.read(
            **kwargs
        )
        if isinstance(
                data,
                mfm.experiments.data.ExperimentalData
        ):
            data = mfm.experiments.data.ExperimentDataGroup([data])
        if isinstance(
                data,
                mfm.experiments.data.ExperimentDataGroup
        ):
            for d in data:
                d.experiment = self.experiment
                d.setup = self
        return data


class ExperimentReaderController(
    mfm.base.Base
):

    @property
    def experiment_reader(
            self
    ) -> ExperimentReader:
        return self._experiment_reader

    @experiment_reader.setter
    def experiment_reader(
            self,
            v: ExperimentReader
    ):
        self._experiment_reader = v

    def __init__(
            self,
            experiment_reader: ExperimentReader,
            *args,
            **kwargs
    ):
        super().__init__(
            *args,
            **kwargs
        )
        self._experiment_reader = experiment_reader
        self._call_dict = dict()
        experiment_reader.controller = self

    def add_call(
            self,
            call_name: str,
            call_function: Callable,
            call_parameters: Dict
    ):
        self._call_dict[call_name] = {
            'call_function': call_function,
            'call_parameters': call_parameters
        }

    def remove_call(
            self,
            call_name: str
    ):
        self._call_dict.pop(
            call_name
        )

    def call(
            self,
            call_name: str
    ) -> None:
        call_function = self._call_dict[call_name]['call_function']
        call_parameters = self._call_dict[call_name]['call_parameters']
        call_function(**call_parameters)

    def __getattr__(
            self,
            item: str
    ):
        return self._experiment_reader.__getattribute__(
            item
        )

    @abstractmethod
    def get_filename(
            self
    ) -> str:
        pass
