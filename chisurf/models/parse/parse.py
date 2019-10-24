from __future__ import annotations
from typing import List

import os

import yaml
from numpy import *
# from collections import defaultdict
# import sympy
# import sympy.printing.latex
# import sympy.parsing.sympy_parser
from re import Scanner

from qtpy import QtCore, QtWidgets, QtSvg

import chisurf.decorators
import chisurf.widgets
import chisurf.parameter
import chisurf.fio
from chisurf.models.model import ModelWidget, ModelCurve
from chisurf.fitting.parameter import FittingParameter, FittingParameterGroup

#
# class GenerateSymbols(defaultdict):
#
#     def __missing__(self, key):
#         print(key)
#         return sympy.Symbol(key)
#

class ParseFormula(
    FittingParameterGroup
):

    def __init__(
            self,
            fit: chisurf.fitting.fit.Fit = None,
            model: chisurf.models.model.Model = None,
            short: str = '',
            **kwargs
    ):
        super().__init__(
            fit=fit,
            model=model,
            short=short,
            **kwargs
        )

        self._keys = list()
        self._models = dict()
        self._count = 0
        self._func = "x*0"
        self.code = self._func

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, v):
        self._func = v
        self.parse_code()

    def parse_code(self):

        def var_found(
                scanner,
                name: str
        ):
            if name in ['caller', 'e', 'pi']:
                return name
            if name not in self._keys:
                self._keys.append(name)
                ret = 'a[%d]' % self._count
                self._count += 1
            else:
                ret = 'a[%d]' % (self._keys.index(name))
            return ret

        code = self._func
        scanner = Scanner([
            (r"x", lambda y, x: x),
            (r"[a-zA-Z]+\.", lambda y, x: x),
            (r"[a-z]+\(", lambda y, x: x),
            (r"[a-zA-Z_]\w*", var_found),
            (r"\d+\.\d*", lambda y, x: x),
            (r"\d+", lambda y, x: x),
            (r"\+|-|\*|/", lambda y, x: x),
            (r"\s+", None),
            (r"\)+", lambda y, x: x),
            (r"\(+", lambda y, x: x),
            (r",", lambda y, x: x),
        ])
        self._count = 0
        self._keys = list()
        parsed, rubbish = scanner.scan(code)
        parsed = ''.join(parsed)
        if rubbish != '':
            raise Exception('parsed: %s, rubbish %s' % (parsed, rubbish))
        self.code = parsed

        # Define parameters
        self._parameters = list()
        for key in self._keys:
            p = FittingParameter(name=key, value=1.0)
            self._parameters.append(p)

    def find_parameters(
            self,
            parameter_type=chisurf.parameter.Parameter
    ):
        # do nothing
        pass


class ParseModel(
    ModelCurve
):

    name = "Parse-Model"

    def __init__(
            self,
            fit: chisurf.fitting.fit.FitGroup,
            *args,
            **kwargs
    ):
        super().__init__(
            fit,
            *args,
            **kwargs
        )
        self.parse = ParseFormula()

    def update_model(self, **kwargs):
        a = [p.value for p in self.parse.parameters]
        x = self.fit.data.x
        try:
            y = eval(self.parse.code)
        except:
            y = zeros_like(x) + 1.0
        self._y = y


class ParseFormulaWidget(
    QtWidgets.QWidget
):

    @chisurf.decorators.init_with_ui(
        ui_filename="parseWidget.ui"
    )
    def __init__(
            self,
            n_columns: int = None,
            model_file: str = None,
            model_name: str = None,
            model: chisurf.models.model.Model = None
    ):
        self.model = model
        if n_columns is None:
            n_columns = chisurf.settings.gui['fit_models']['n_columns']
        self.n_columns = n_columns

        self.actionFormulaChanged.triggered.connect(self.onEquationChanged)
        self.actionModelChanged.triggered.connect(self.onModelChanged)

        self._models = {}
        if model_file is None:
            model_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'models.yaml'
            )
        self._model_file = model_file
        self.load_model_file(model_file)

        if model_name is None:
            model_name = list(self._models)[0]
        self.model_name = model_name
        self.svg_equation = QtSvg.QSvgWidget()
        self.verticalLayout.addWidget(self.svg_equation)

    def load_model_file(self, filename):
        with chisurf.fio.zipped.open_maybe_zipped(
                filename=filename,
                mode='r'
        ) as fp:
            self._model_file = filename
            self.models = yaml.safe_load(fp)

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, v):
        self._models = v
        self.comboBox.clear()
        self.comboBox.addItems(list(v.keys()))

    @property
    def model_name(self) -> List[str]:
        return list(self.models.keys())[self.comboBox.currentIndex()]

    @model_name.setter
    def model_name(
            self,
            v: str
    ):
        idx = self.comboBox.findText(v)
        self.comboBox.setCurrentIndex(idx)

    @property
    def model_file(self):
        return self._model_file

    @model_file.setter
    def model_file(self, v):
        self._model_file = v
        self.load_model_file(v)

    def onUpdateFunc(self):
        function_str = str(self.plainTextEdit.toPlainText())
        chisurf.run(
            "\n".join(
                [
                    "cs.current_fit.model.parse.func = '%s'" % function_str,
                    "cs.current_fit.update()"
                ]
            )
        )
        try:
            ivs = self.models[self.model_name]['initial']
            for key in ivs.keys():
                self.model.parameter_dict[key].value = ivs[key]
        except AttributeError:
            print("No initial values")

        #
        # # d = GenerateSymbols()
        # print(function_str)
        # try:
        #     #expr = eval(function_str, d)
        #     tex = sympy.printing.latex(
        #         sympy.parsing.sympy_parser.parse_expr(
        #             function_str
        #         )
        #     )
        #     print(tex)
        #     self.svg_equation.load(
        #         chisurf.widgets.tex2svg(
        #             tex
        #         )
        #     )
        # except:
        #     print("erre")

    def onModelChanged(self):
        func = self.models[self.model_name]['equation']
        self.plainTextEdit.setPlainText(
            func
        )
        self.textEdit.setHtml(
            self.models[self.model_name]['description']
        )
        self.onUpdateFunc()
        self.onEquationChanged()

    def onEquationChanged(self):
        self.onUpdateFunc()
        layout = self.gridLayout_2
        chisurf.widgets.clear_layout(layout)
        n_columns = self.n_columns
        row = 1
        for i, p in enumerate(self.model.parameters):
            pw = chisurf.fitting.widgets.make_fitting_parameter_widget(
                fitting_parameter=p
            )
            column = i % n_columns
            if column == 0:
                row += 1
            layout.addWidget(pw, row, column)

    def onLoadModelFile(
            self,
            filename: str = None
    ):
        if filename is None:
            filename = chisurf.widgets.get_filename(
                'Open models-file',
                'link file (*.yaml)'
            )
        self.load_model_file(filename)


class ParseModelWidget(
    ParseModel,
    ModelWidget
):

    def __init__(
            self,
            fit: chisurf.fitting.fit.FitGroup,
            *args,
            **kwargs
    ):
        super().__init__(
            fit,
            *args,
            **kwargs
        )
        parse = ParseFormulaWidget(
            model=self
        )
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.addWidget(
            parse
        )
        self.setLayout(
            layout
        )

    def update_model(self, **kwargs):
        ParseModel.update_model(self, **kwargs)

