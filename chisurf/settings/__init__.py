from __future__ import annotations

import os
import datetime
import sys
import yaml
import json
import shutil

#######################################################
#        SETTINGS  & CONSTANTS                        #
#######################################################

package_directory = os.path.dirname(
    os.path.abspath(__file__)
)

home = os.path.expanduser("~")
path = os.path.abspath(os.path.join(home, '.chisurf'))
if not os.path.isdir(path):
    os.makedirs(path)

# Open chisurf settings file
chisurf_settings_file = os.path.abspath(
    os.path.join(
        home,
        '.chisurf/settings_chisurf.yaml')
)
# If settings file does not exist in user folder
# copy settings file from program directory
if not os.path.isfile(chisurf_settings_file):
    original_settings = os.path.join(
            package_directory, 'settings_chisurf.yaml'
        )
    shutil.copyfile(
        original_settings,
        chisurf_settings_file
    )
with open(chisurf_settings_file) as fp:
    cs_settings = yaml.safe_load(fp)

# Open color settings file
color_settings_file = os.path.join(
        home,
        '.chisurf/settings_colors.yaml'
)
# If settings file does not exist in user folder
# copy settings file from program directory
if not os.path.isfile(color_settings_file):
    original_colors = os.path.join(
            package_directory, 'settings_colors.yaml'
        )
    shutil.copyfile(
        original_colors,
        color_settings_file
    )
with open(color_settings_file) as fp:
    colors = yaml.safe_load(fp)


gui = cs_settings['gui']
parameter = cs_settings['parameter']
fitting = cs_settings['fitting']
fret = cs_settings['fret']
tcspc = cs_settings['tcspc']
package_directory = os.path.dirname(os.path.abspath(__file__))
eps = sys.float_info.epsilon
working_path = ''

style_sheet_file = os.path.join(
    package_directory,
    './gui/styles/',
    gui['style_sheet']
)

with open(os.path.join(
        package_directory,
        './constants/structure.json')
) as fp:
    structure_data = json.load(fp)


session_str = datetime.datetime.now().strftime('session_%H_%M_%d_%m_%Y')

home = os.path.expanduser("~")
path = os.path.abspath(os.path.join(home, '.chisurf'))
if not os.path.isdir(path):
    os.makedirs(path)

session_file = os.path.join(path, session_str + ".py")
session_log = os.path.join(path, session_str + ".log")

url = 'https://github.com/Fluorescence-Tools/chisurf'
