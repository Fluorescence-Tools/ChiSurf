"""

"""
from __future__ import annotations
from typing import Tuple, Callable, Dict

from abc import abstractmethod, abstractproperty

import chisurf.base
import chisurf.curve
import chisurf.experiments


class ExperimentReader(
    chisurf.base.Base
):

    def __init__(
            self,
            experiment: chisurf.experiments.experiment.Experiment,
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
        self.controller = controller

    @abstractmethod
    def autofitrange(
            self,
            data: chisurf.base.Data,
            **kwargs
    ) -> Tuple[int, int]:
        return 0, len(data.y) - 1

    @abstractmethod
    def read(
            self,
            name: str = None,
            *args,
            **kwargs
    ) -> chisurf.base.Data:
        """

        :param name: A name that will be associated to the data set that is read.
        :param kwargs:
        :return:
        """
        pass

    def get_data(
            self,
            **kwargs
    ) -> chisurf.experiments.data.ExperimentDataGroup:
        data = self.read(
            **kwargs
        )
        if isinstance(
                data,
                chisurf.experiments.data.ExperimentalData
        ):
            data = chisurf.experiments.data.ExperimentDataGroup([data])
        if isinstance(
                data,
                chisurf.experiments.data.ExperimentDataGroup
        ):
            for d in data:
                d.experiment = self.experiment
                d.setup = self
        return data


class ExperimentReaderController(
    chisurf.base.Base
):

    def __init__(
            self,
            experiment_reader: ExperimentReader = None,
            *args,
            **kwargs
    ):
        super().__init__(
            *args,
            **kwargs
        )
        self.experiment_reader = experiment_reader
        self._call_dict = dict()
        if isinstance(
                experiment_reader,
                ExperimentReader
        ):
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

    @abstractproperty
    def filename(
            self
    ) -> str:
        pass

    @abstractmethod
    def get_filename(
            self
    ) -> str:
        pass
