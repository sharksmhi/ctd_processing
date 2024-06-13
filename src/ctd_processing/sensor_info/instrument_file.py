import pandas as pd
import pathlib
import openpyxl

import logging


logger = logging.getLogger(__name__)


class InstrumentFile:
    def __init__(self, file_path):
        self._path = pathlib.Path(file_path)

        self._wb = openpyxl.load_workbook(self._path)
        self._sheets = self._wb.sheetnames

        self._info = {}

        self._save_info()
        # self._add_cnv_code_to_pars()

    def __str__(self):
        return f'InstrumentFile: {self._path}'

    def _save_info(self):
        self._info = {}
        # df = pd.read_excel(self._path, sheet_name='Instrument.xls', engine='openpyxl', skiprows=[0])
        df = pd.read_excel(self._path, sheet_name='Sensor_info', engine='openpyxl', skiprows=[0])
        df = df.fillna('')
        for i in df.index:
            data = df.iloc[i].to_dict()
            cnv_name = str(df.iloc[i]['CNV_NAME'])
            if cnv_name == '':
                continue
            cnv_codes = [item.strip() for item in str(df.iloc[i]['CNV_CODE']).split(',')]
            data['cnv_codes'] = cnv_codes
            sensor_string = str(df.iloc[i]['SENSOR_ID'])
            if sensor_string == '':
                for code in cnv_codes:
                    if code == '':
                        continue
                    data['CNV_NAME'] = code
                    self._info[code] = data
            else:
                self._info.setdefault(cnv_name, {})
                sensor_list = [item.strip() for item in sensor_string.split(',')]
                for sensor in sensor_list:
                    self._info[cnv_name][sensor] = data

    def _add_cnv_code_to_pars(self):
        """ Adds the cnv_codes as parameters in self._info if only sensor is 'all'"""
        for cnv_name in list(self._info.keys()):
            sensor_keys = list(self._info[cnv_name].keys())
            if len(sensor_keys) != 1:
                continue
            if sensor_keys[0] != 'all':
                continue
            for cnv_code in self._info[cnv_name]['all'].get('cnv_codes', []):
                if not cnv_code:
                    continue
                self._info[cnv_code] = self._info[cnv_name]['all']

    def get_info_for_parameter_and_sensor_id(self, parameter, sensor_id=None):
        """ Returns information from self._info. Matches key in self._info where key is part of "parameter" """
        for key, info in self._info.items():
            logger.debug(f'key: {key}')
            # logger.debug(f'type(key): {type(key)}')
            logger.debug(f'par: {parameter}')
            logger.debug(f'sensor_id: {sensor_id}')
            if key == parameter and sensor_id is None:
                return info
            if key in parameter and sensor_id:
                return info.get(str(sensor_id))
