# -*- coding: utf-8 -*-
"""
Created on 2020-05-08 10:36

@author: a002028


Ref: https://stackoverflow.com/questions/55049175/running-bokeh-server-on-local-network

In a conda-prompt run:
    cd "PATH_TO_THIS_SCRIPT"
    bokeh serve app_to_serve.py

Open in web browser: http://localhost:5006/app_to_serve
    Bokeh app running at: http://localhost:5006/app_to_serve

"""
from bokeh.plotting import curdoc
from ctdvis.session import Session

DATA_DIR = ''
MONTH_LIST = []
SHIP_LIST = []
SERNO_MIN = []
SERNO_MAX = []

VISUALIZE_SETTINGS = 'smhi_vis'

URL = 'http://localhost:5006/'


def bokeh_qc_tool():
    """ Filters are advised to be implemented if the datasource is big, (~ >3 months of SMHI-EXP-data) """
    filters = {}
    if MONTH_LIST:
        filters['month_list'] = MONTH_LIST
    if SHIP_LIST:
        filters['ship_list'] = SHIP_LIST
    if SERNO_MIN:
        filters['serno_min'] = SERNO_MIN
    if SERNO_MAX:
        filters['serno_max'] = SERNO_MAX

    visualize_setting = 'smhi_vis'
    if VISUALIZE_SETTINGS:
        visualize_setting = VISUALIZE_SETTINGS

    s = Session(visualize_setting=visualize_setting, data_directory=DATA_DIR, filters=filters)
    s.setup_datahandler()
    layout = s.run_tool(return_layout=True)

    return layout


bokeh_layout = bokeh_qc_tool()
doc = curdoc()
doc.add_root(bokeh_layout)
