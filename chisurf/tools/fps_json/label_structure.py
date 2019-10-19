"""
This module contain a small tool to generate JSON-labeling files
"""
from __future__ import annotations

import sys
import json
from collections import OrderedDict
import traceback

from qtpy import QtWidgets, QtCore
import qdarkstyle

import chisurf.settings as mfm
import chisurf.fio
import chisurf.widgets
import chisurf.widgets.pdb
import chisurf.widgets.accessible_volume
import chisurf.decorators
import chisurf.structure
import chisurf.structure.structure


class LabelStructure(
    QtWidgets.QWidget
):

    name = "LabelStructure"

    @chisurf.decorators.init_with_ui(ui_filename="fps_json_edit.ui")
    def __init__(
            self,
            *args,
            **kwargs
    ):
        self.atom_select = chisurf.widgets.pdb.PDBSelector()
        self.verticalLayout_3.addWidget(self.atom_select)
        self.av_properties = chisurf.widgets.accessible_volume.AVProperties()
        self.verticalLayout_4.addWidget(self.av_properties)

        self.textEdit_2 = chisurf.widgets.text_editor.SimpleCodeEditor(
            language='JSON'
        )
        self.tab_2.layout().addWidget(self.textEdit_2)

        self.toolButton_4.clicked.connect(self.onLoadReferencePDB)
        self.pushButton_2.clicked.connect(self.onAddLabel)
        self.pushButton_3.clicked.connect(self.onAddDistance)
        self.actionSave.triggered.connect(self.onSaveLabelingFile)
        self.actionClear.triggered.connect(self.onClear)
        self.actionLoad.triggered.connect(self.onLoadJSON)
        self.actionReadTextEdit.triggered.connect(self.onReadTextEdit)
        self.actionRemoveLabelingPosition.triggered.connect(
            self.onLabelingListDoubleClicked
        )
        self.actionRemove_distance.triggered.connect(
            self.onDistanceListDoubleClicked
        )
        self.comboBox.currentIndexChanged[int].connect(
            self.onSimulationTypeChanged
        )

        self.structure = None
        self.json_file = None
        self.positions = OrderedDict()
        self.distances = OrderedDict()

    def onReadTextEdit(self):
        s = str(self.textEdit_2.text())
        try:
            p = json.loads(s)
            self.distances = p["Distances"]
            self.positions = p["Positions"]
            self.onUpdateJSON()
            self.onUpdateInterface()
        except json.decoder.JSONDecodeError:
            chisurf.widgets.widgets.MyMessageBox(
                info="There is a problem parsing the JSON file.\n",
                details=traceback.format_exc()
            )

    def onLoadJSON(self):
        filename = chisurf.widgets.get_filename(
            'Open JSON Labeling-File',
            'JSON-Files (*.fps.json)'
        )
        try:
            self.json_file = filename
            p = json.load(
                chisurf.fio.zipped.open_maybe_zipped(
                    filename=self.json_file,
                    mode='r'
                )
            )
            self.distances = p["Distances"]
            self.positions = p["Positions"]
            self.onUpdateJSON()
            self.onUpdateInterface()
        except (FileExistsError, FileNotFoundError):
            chisurf.widgets.widgets.MyMessageBox(
                info="There is a problem opening the JSON file.\n",
                details=traceback.format_exc()
            )

    def onLabelingListDoubleClicked(
            self,
            event: QtCore.QEvent,
    ):
        item = self.listWidget.currentItem()
        label_name = str(item.text())
        del self.positions[label_name]
        for dist in list(self.distances.values()):
            if dist['position1_name'] == label_name or dist['position1_name'] == label_name:
                del dist
        self.onUpdateInterface()
        self.onUpdateJSON()

    def onDistanceListDoubleClicked(
            self,
            event: QtCore.QEvent,
    ):
        item = self.listWidget_2.currentItem()
        distance_name = str(item.text())
        del self.distances[distance_name]
        self.onUpdateInterface()
        self.onUpdateJSON()

    def onSimulationTypeChanged(self):
        self.av_properties.av_type = self.simulation_type

    def onUpdateInterface(self):
        self.comboBox_2.clear()
        self.comboBox_4.clear()
        self.listWidget.clear()
        self.listWidget_2.clear()
        label_names = [label for label in list(self.positions.keys())]
        distance_names = [label for label in list(self.distances.keys())]
        self.listWidget.addItems(label_names)
        self.listWidget_2.addItems(distance_names)
        self.comboBox_2.addItems(label_names)
        self.comboBox_4.addItems(label_names)

    @property
    def distance_type(self) -> str:
        distance_type = str(self.comboBox_3.currentText())
        if distance_type == 'dRDA':
            return 'RDAMean'
        elif distance_type == 'dRDAE':
            return 'RDAMeanE'
        elif distance_type == 'dRmp':
            return 'Rmp'
        elif distance_type == 'pRDA':
            return 'pRDA'

    @property
    def label1(self) -> str:
        return str(self.comboBox_2.currentText())

    @property
    def label2(self) -> str:
        return str(self.comboBox_4.currentText())

    @property
    def distance(self) -> float:
        return float(self.doubleSpinBox.value())

    @property
    def forster_radius(self) -> float:
        return float(self.doubleSpinBox_4.value())

    @property
    def error_pos(self) -> float:
        return float(self.doubleSpinBox_2.value())

    @property
    def error_neg(self) -> float:
        return float(self.doubleSpinBox_3.value())

    @property
    def pdb_filename(self) -> str:
        return str(self.lineEdit.text())

    @pdb_filename.setter
    def pdb_filename(
            self,
            v: str
    ):
        self.lineEdit.setText(str(v))

    @property
    def simulation_type(self) -> str:
        return str(self.comboBox.currentText())

    @property
    def position_name(self) -> str:
        return str(self.lineEdit_2.text())

    def onLoadReferencePDB(self):
        filename = chisurf.widgets.get_filename(
            'Open PDB-File',
            'PDB-Files (*.pdb);;PDB-GZ (*.pdb.gz)'
        )
        self.pdb_filename = filename
        self.structure = mfm.structure.structure.Structure(self.pdb_filename)
        self.atom_select.atoms = self.structure.atoms

    def onAddLabel(self):
        try:
            label = {
                "atom_name": str(self.atom_select.atom_name),
                "chain_identifier": str(self.atom_select.chain_id),
                "residue_seq_number": int(self.atom_select.residue_id),
                "residue_name": str(self.atom_select.residue_name),
                "attachment_atom_index": int(self.atom_select.atom_number),
                "simulation_type": str(self.simulation_type),
                "linker_length": float(self.av_properties.linker_length),
                "linker_width": float(self.av_properties.linker_width),
                "radius1": float(self.av_properties.radius_1),
                "radius2": float(self.av_properties.radius_2),
                "radius3": float(self.av_properties.radius_3),
                "simulation_grid_resolution": float(self.av_properties.resolution)
            }
            if self.position_name != '' and self.position_name not in list(self.positions.keys()):
                self.positions[self.position_name] = label
                self.onUpdateInterface()
                self.onUpdateJSON()
        except (ValueError, TypeError):
            chisurf.widgets.widgets.MyMessageBox(
                info="Could not add labeling position.\n",
                details=traceback.format_exc()
            )

    def onAddDistance(self):
        distance = {
            "Forster_radius": self.forster_radius,
            "distance_type": self.distance_type,
            "position1_name": self.label1,
            "position2_name": self.label2,
        }

        if self.distance_type == "pRDA":
            fn = chisurf.widgets.get_filename(
                "DA-Distance distribution (1st column RDA, 2nd pRDA)"
            )
            csv = chisurf.fio.ascii.Csv(
                filename=fn,
                skiprows=1
            )
            distance['rda'] = list(csv.data[0])
            distance['prda'] = list(csv.data[1])
        else:
            distance['distance'] = self.distance
            distance['error_neg'] = self.error_neg
            distance['error_pos'] = self.error_pos

        distance_name = self.label1+'_'+self.label2
        self.distances[distance_name] = distance
        self.onUpdateInterface()
        self.onUpdateJSON()

    def onSaveLabelingFile(
            self,
            event: QtCore.QEvent = None
    ):
        filename = chisurf.widgets.save_file(
            'Open FPS-JSON File',
            'JSON-Files (*.fps.json)'
        )
        try:
            with open(
                    file=filename,
                    mode='w'
            ) as fp:
                fp.write(
                    self.textEdit_2.text()
                )
            self.json_file = filename
        except (FileNotFoundError, FileExistsError):
            chisurf.widgets.widgets.MyMessageBox(
                info="There is a problem saving the JSON file.\n",
                details=traceback.format_exc()
            )

    def onUpdateJSON(self):
        p = OrderedDict()
        p["Distances"] = self.distances
        p["Positions"] = self.positions
        s = json.dumps(
            p,
            sort_keys=True,
            indent=4, separators=(',', ': ')
        )
        self.textEdit_2.clear()
        self.textEdit_2.setText(s)

    def onClear(self):
        reply = chisurf.widgets.widgets.MyMessageBox.question(
            self,
            'Message',
            "Are you sure you want to clear all fields?",
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.positions = OrderedDict()
            self.distances = OrderedDict()
            self.onUpdateInterface()
            self.onUpdateJSON()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = LabelStructure()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    win.show()
    sys.exit(app.exec_())
