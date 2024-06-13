#!/usr/bin/env python3
# Copyright (c) 2020 SMHI, Swedish Meteorological and Hydrological Institute.
# License: MIT License (see LICENSE.txt or http://opensource.org/licenses/mit).
"""
Created on 2021-12-29 17:19

@author: johannes

Ref: https://stackoverflow.com/questions/55049175/running-bokeh-server-on-local-network
"""
import json
from pathlib import Path
from bokeh.plotting import curdoc
from ctdvis.session import Session


def bokeh_qc_tool():
    """Return bokeh app layout.

    kwargs are taken from the temporary session file 'session_ctd_qc_arguments.json'
    kwargs = {
        data_directory (str): Path to CTD-standard-format (including auto-QC-fields).
        visualize_setting (str): Visualize setting eg. smhi_vis | deep_vis | umsc_vis
        filters (dict | None): As of now only month filter eg. {'month_list': [1,2,3]}.
                               Functionality of filter on ship and/or serno is also possible,
                               but not yet implemented in this script.
                               Option to filter on file_names /MW 2022-09-06
    }

    Filters are advised to be implemented if the datasource is big, (~ >3 months of SMHI-EXP-data)
    filters = dict(
        # month_list=[1, 2, 3],
        # ship_list=['77SE', '34AR']
        # serno_min=311,
        # serno_max=355,
    )
    """
    session_settings_path = Path(Path(__file__).parent, 'session_ctd_qc_arguments.json')
    with open(session_settings_path, 'r') as f:
        kwargs = json.load(f)

    export_folder = None
    if 'export_folder' in kwargs:
        export_folder = kwargs.pop('export_folder')

    s = Session(**kwargs)
    s.setup_datahandler()
    layout = s.run_tool(return_layout=True,
                        export_folder=export_folder)
    return layout


bokeh_layout = bokeh_qc_tool()
doc = curdoc()
doc.add_root(bokeh_layout)
