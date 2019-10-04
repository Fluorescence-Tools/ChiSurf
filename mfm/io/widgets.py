from __future__ import annotations

import os
from qtpy import QtWidgets

import mfm
import mfm.decorators
import mfm.base
import mfm.structure.structure
import mfm.widgets

from . import photons
from . import tttr


class SpcFileWidget(
    QtWidgets.QWidget
):

    @mfm.decorators.init_with_ui(ui_filename="spcSampleSelectWidget.ui")
    def __init__(
            self,
            *args,
            **kwargs,
    ):
        self._photons = None
        self.filenames = list()
        self.filetypes = tttr.filetypes

        self.actionSample_changed.triggered.connect(self.onSampleChanged)
        self.actionLoad_sample.triggered.connect(self.onLoadSample)
        #self.connect(self.comboBox_2, QtCore.SIGNAL("currentIndexChanged(int)"), self.onFileTypeChanged)

    @property
    def sample_name(self) -> str:
        try:
            return self.filename
        except AttributeError:
            return "--"

    @property
    def dt(self) -> float:
        return float(self.doubleSpinBox.value())

    @dt.setter
    def dt(
            self,
            v: float
    ):
        self.doubleSpinBox.setValue(v)

    def onSampleChanged(self):
        index = 0 # TODO: fix multiple samples per HDF self.comboBox.currentIndex()
        self._photons.sample = self.samples[index]
        self.dt = float(self._photons.mt_clk / self._photons.n_tac) * 1e6
        self.nTAC = self._photons.n_tac
        self.nROUT = self._photons.n_rout
        self.number_of_photons = self._photons.nPh
        self.measurement_time = self._photons.measurement_time
        self.lineEdit_7.setText("%.2f" % self.count_rate)

    @property
    def measurement_time(
            self
    ) -> float:
        return float(self._photons.measurement_time)

    @measurement_time.setter
    def measurement_time(
            self,
            v: float
    ):
        self.lineEdit_6.setText("%.1f" % v)

    @property
    def number_of_photons(
            self
    ) -> int:
        return int(self.lineEdit_5.value())

    @number_of_photons.setter
    def number_of_photons(
            self,
            v: int
    ):
        self.lineEdit_5.setText(str(v))

    @property
    def rep_rate(
            self
    ) -> float:
        return float(self.doubleSpinBox_2.value())

    @rep_rate.setter
    def rep_rate(
            self,
            v: float
    ):
        self.doubleSpinBox_2.setValue(v)

    @property
    def nROUT(
            self
    ) -> int:
        return int(self.lineEdit_3.text())

    @nROUT.setter
    def nROUT(
            self,
            v: int
    ):
        self.lineEdit_3.setText(str(v))

    @property
    def nTAC(
            self
    ) -> int:
        return int(self.lineEdit.text())

    @nTAC.setter
    def nTAC(
            self,
            v: int
    ):
        self.lineEdit.setText(str(v))

    """
    @property
    def filetypes(self):
        return self._file_types

    @filetypes.setter
    def filetypes(self, v):
        self._file_types = v
        #self.comboBox_2.addItems(list(v.keys()))
    """

    @property
    def count_rate(
            self
    ) -> float:
        return self._photons.nPh / float(self._photons.measurement_time) / 1000.0

    def onFileTypeChanged(self):
        self._photons = None
        #self.comboBox.clear()
        #if self.fileType == "hdf":
        #    self.comboBox.setDisabled(False)
        #else:
        #    self.comboBox.setDisabled(True)

    @property
    def fileType(
            self
    ) -> str:
        return "hdf"
        #return str(self.comboBox_2.currentText())

    @property
    def filename(
            self
    ) -> str:
        try:
            return self.filenames[0]
        except:
            return "--"

    def onLoadSample(
            self
    ) -> None:
        if self.fileType in ("hdf"):
            filename = mfm.widgets.get_filename(
                'Open Photon-HDF',
                'Photon-HDF (*.photon.h5)'
            )
            filenames = [filename]
            self.lineEdit_2.setText(filename)
        elif self.fileType in ("ht3"):
            filename = mfm.widgets.open_file(
                'Open Photon-HDF',
                'Photon-HDF (*.ht3)'
            )
            filenames = [filename]
        else:
            directory = mfm.widgets.get_directory()
            filenames = [directory + '/' + s for s in os.listdir(directory)]

        self.filenames = filenames
        self._photons = photons.Photons(filenames, self.fileType)
        self.samples = self._photons.samples
        #self.comboBox.addItems(self._photons.sample_names)
        self.onSampleChanged()

    @property
    def photons(
            self
    ) -> photons.Photons:
        return self._photons


class PDBLoad(QtWidgets.QWidget):

    @mfm.decorators.init_with_ui(ui_filename="proteinMCLoad.ui")
    def __init__(self, *args, **kwargs):
        self._data = None
        self._filename = ''

    def load(self, filename=None):
        if filename is None:
            filename = mfm.widgets.get_filename(
                'Open PDB-Structure',
                'PDB-file (*.pdb)'
            )
        self.filename = filename
        self.structure = self.filename
        self.lineEdit.setText(str(self.structure.n_atoms))
        self.lineEdit_2.setText(str(self.structure.n_residues))

    @property
    def filename(self):
        return str(self.lineEdit_7.text())

    @filename.setter
    def filename(self, v):
        self.lineEdit_7.setText(v)

    @property
    def calcLookUp(self):
        return self.checkBox.isChecked()

    @property
    def structure(self):
        return self._data

    @structure.setter
    def structure(self, v):
        self._data = mfm.structure.structure.Structure(
            v,
            make_coarse=self.calcLookUp
        )


class CsvWidget(
    mfm.base.Base,
    QtWidgets.QWidget
):

    @mfm.decorators.init_with_ui(ui_filename="csvInput.ui")
    def __init__(
            self,
            *args,
            **kwargs
    ):
        self.actionUseHeader.triggered.connect(self.changeCsvParameter)
        self.actionSkiprows.triggered.connect(self.changeCsvParameter)
        self.actionColspecs.triggered.connect(self.changeCsvParameter)
        self.actionCsvType.triggered.connect(self.changeCsvParameter)
        self.actionSetError.triggered.connect(self.changeCsvParameter)
        self.actionColumnsChanged.triggered.connect(
            self.changeCsvParameter
        )
        self.verbose = kwargs.get('verbose', mfm.verbose)

    def changeCsvParameter(self):
        set_errx_on = bool(self.checkBox_3.isChecked())
        set_erry_on = bool(self.checkBox_4.isChecked())
        colspecs = str(self.lineEdit.text())
        use_header = bool(self.checkBox_2.isChecked())
        n_skip = int(self.spinBox.value())
        mode = 'csv' if self.radioButton_2.isChecked() else 'fwf'
        mfm.run(
            "\n".join(
                [
                    "cs.current_setup.error_y_on = %s" % set_erry_on,
                    "cs.current_setup.error_x_on = %s" % set_errx_on,
                    "cs.current_setup.colspecs = '%s'" % colspecs,
                    "cs.current_setup.use_header = %s" % use_header,
                    "cs.current_setup.skiprows = %s" % n_skip,
                    "cs.current_setup.reading_routine = '%s'" % mode,
                    "cs.current_setup.col_ey = %s" % self.spinBox_5.value(),
                    "cs.current_setup.col_ex = %s" % self.spinBox_3.value(),
                    "cs.current_setup.col_x = %s" % self.spinBox_2.value(),
                    "cs.current_setup.col_y = %s" % self.spinBox_4.value()
                ]
            )
        )

    @property
    def filename(self) -> str:
        return str(self.lineEdit_8.text())

    @filename.setter
    def filename(
            self,
            v: str
    ):
        self.lineEdit_8.setText(v)


# To be deleted
#
# class CSVFileWidget(QtWidgets.QWidget):
#
#     def __init__(
#             self,
#             *args,
#             **kwargs
#     ):
#         super().__init__(
#             *args,
#             **kwargs
#         )
#
#         layout = QtWidgets.QVBoxLayout(self)
#         layout.setSpacing(0)
#         layout.setContentsMargins(0, 0, 0, 0)
#
#         self.layout = layout
#         self.csvWidget = CsvWidget(**kwargs)
#         self.layout.addWidget(self.csvWidget)
#
#     def load_data(
#             self,
#             filename: str = None
#     ) -> mfm.experiment.data.DataCurve:
#         """
#         Loads csv-data into a Curve-object
#         :param filename:
#         :return: Curve-object
#         """
#         d = mfm.experiment.data.DataCurve(setup=None)
#         if filename is not None:
#             self.csvWidget.load(filename)
#             d.filename = filename
#         else:
#             self.csvWidget.load()
#             d.filename = self.csvWidget.filename
#
#         d.x, d.y = self.csvWidget.data_x, self.csvWidget.data_y
#         if self.weight_calculation is None:
#             d.set_weights(self.csvWidget.error_y)
#         else:
#             d.set_weights(self.weight_calculation(d.y))
#         return d
#
#     def get_data(self, *args, **kwargs):
#         return self.load_data(*args, **kwargs)

