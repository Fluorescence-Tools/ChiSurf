from PyQt5 import QtWidgets, uic

from mfm.fluorescence import lifetime2transfer, transfer2distance, distance2transfer, transfer2lifetime, \
    fretrate2distance, distance2fretrate


class FRETCalculator(QtWidgets.QWidget):

    name = "FRET-Calculator"

    def __init__(self, kappa2=0.667):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi('./mfm/ui/tools/calc_tau2r.ui', self)
        self.kappa2 = kappa2
        ## User-interface
        self.doubleSpinBox.editingFinished.connect(self.onTau0Changed)
        self.doubleSpinBox_2.editingFinished.connect(self.onTauChanged)
        self.doubleSpinBox_3.editingFinished.connect(self.onR0Changed)
        self.doubleSpinBox_9.editingFinished.connect(self.onRChanged)
        self.doubleSpinBox_4.editingFinished.connect(self.onEChanged)
        self.doubleSpinBox_5.editingFinished.connect(self.onkFRETChanged)
        self.onkFRETChanged()
        self.hide()

    def onRChanged(self):
        self.blockSignals(True)
        self.kFRET = distance2fretrate(self.R, self.R0, self.tau0, 2. / 3.)
        self.E = distance2transfer(self.R, self.R0)
        self.tau = transfer2lifetime(self.E, self.tau0)
        self.blockSignals(False)

    def onkFRETChanged(self):
        self.blockSignals(True)
        self.R = fretrate2distance(self.kFRET, self.R0, self.tau0)
        self.E = distance2transfer(self.R, self.R0)
        self.tau = transfer2lifetime(self.E, self.tau0)
        self.blockSignals(False)

    def onTauChanged(self):
        self.blockSignals(True)
        self.E = lifetime2transfer(self.tau, self.tau0)
        self.R = fretrate2distance(self.kFRET, self.R0, self.tau0)
        self.kFRET = distance2fretrate(self.R, self.R0, self.tau0)
        self.blockSignals(False)

    def onEChanged(self):
        self.blockSignals(True)
        self.R = transfer2distance(self.E, self.R0)
        self.kFRET = distance2fretrate(self.R, self.R0, self.tau0)
        self.tau = transfer2lifetime(self.E, self.tau0)
        self.blockSignals(False)

    def onTau0Changed(self):
        self.blockSignals(True)
        self.E = distance2transfer(self.R, self.R0)
        self.tau = transfer2lifetime(self.E, self.tau0)
        self.kFRET = distance2fretrate(self.R, self.R0, self.tau0)
        self.blockSignals(False)

    def onR0Changed(self):
        self.blockSignals(True)
        self.E = distance2transfer(self.R, self.R0)
        self.tau = transfer2lifetime(self.E, self.tau0)
        self.kFRET = distance2fretrate(self.R, self.R0, self.tau0)
        self.blockSignals(False)


    @property
    def kFRET(self):
        return float(self.doubleSpinBox_5.value())

    @kFRET.setter
    def kFRET(self, value):
        return self.doubleSpinBox_5.setValue(value)

    @property
    def tau0(self):
        return float(self.doubleSpinBox.value())

    @property
    def tau(self):
        return float(self.doubleSpinBox_2.value())

    @tau.setter
    def tau(self, v):
        self.doubleSpinBox_2.setValue(v)

    @property
    def R0(self):
        return float(self.doubleSpinBox_3.value())

    @property
    def R(self):
        return float(self.doubleSpinBox_9.value())

    @R.setter
    def R(self, v):
        self.doubleSpinBox_9.setValue(v)

    @property
    def E(self):
        return float(self.doubleSpinBox_4.value())

    @E.setter
    def E(self, v):
        self.doubleSpinBox_4.setValue(v)
