#!/usr/bin/env bash
$PYTHON setup.py build_ext --inplace --force
$PYTHON setup.py install --single-version-externally-managed --record=record.txt