import os
import pathlib

import file_explorer

from ctd_processing.modify_cnv import ModifyCnv
from ctd_processing.sensor_info import param_reported
from .func import get_sensor_info_columns
from .sensor_info_item import SensorInfoItem


class CreateSensorInfoFile:
    def __init__(self, instrument_file):
        self.instrument_file = instrument_file
        self._stem = None
        self._save_path = None
        self._data = None

    def __str__(self):
        return f'CreateSensorInfoFile: {self._stem}'

    def create_file_from_cnv_file(self, cnv_file_path, **kwargs):
        """
        Created a sensor info file with information in given cnv file.
        The sensor info file is created at the same location as the cnv file.
        """
        path = pathlib.Path(cnv_file_path)
        self._stem = path.stem
        output_dir = path.parent
        self._save_path = pathlib.Path(output_dir, f'{self._stem}.sensorinfo')
        self._save_xml_data_from_cnv(path)
        self._save_file(overwrite=kwargs.get('overwrite'))

    def _save_xml_data_from_cnv(self, path):
        cnv_file = ModifyCnv(path)
        self.cnv_info = []
        self.cnv_info.extend(cnv_file.get_sensor_info())
        self._add_header_information_to_cnv_info(cnv_file)

        self._data = []
        file = file_explorer.get_file_object_for_path(path)

        par_reported = param_reported.ParamReported(path, self.instrument_file)

        pressure_instrument_info = self.instrument_file.get_info_for_parameter_and_sensor_id(parameter='Pressure',
                                                                                             sensor_id=file('instrument_number'))

        columns = [col for col in get_sensor_info_columns() if col not in ['VALIDFR', 'VALIDTO']]
        self._data.append('\t'.join(columns))
        for info in self.cnv_info:
            row_list = []
            instrument_info = self.instrument_file.get_info_for_parameter_and_sensor_id(parameter=info['parameter'],
                                                                                        sensor_id=info['serial_number'])

            if not instrument_info:
                # print('NOT', info['serial_number'], info['parameter'])
                continue

            reported_name = par_reported.get_reported_name(info['parameter'], info['serial_number'])

            # print('instrument_info', instrument_info)
            for col in columns:
                # print('col', col)
                value = str(instrument_info.get(col, '')).strip()
                if col == 'SENSOR_ID':
                    value = info.get('serial_number', '')
                    if value is None:
                        value = ''
                elif col == 'CALIB_DATE':
                    value = info.get('calibration_date', '')
                    if value:
                        value = value.strftime('%Y-%m-%d')
                elif col == 'PARAM_REPORTED':
                    value = reported_name
                    # print('value:PARAM_REPORTED', value, info['parameter'])
                elif col == 'CALCULATED':
                    value = value or 'No'
                elif value:
                    # if col == 'PARAM_SIMPLE':
                    #     print('VALUE', col, value, '===', info['parameter'])
                    # if info['parameter'][-1] == '2':
                    if reported_name.split('[')[0].replace(' ', '').endswith(',2'):
                        if col == 'PARAM_SIMPLE':
                            if value.endswith('*'):
                                value = value.strip('*')
                            else:
                                value = value + '2'
                        elif col == 'PARAM':
                            if value.endswith('*'):
                                value = value.strip('*')
                            else:
                                split_value = value.split('_')
                                split_value[-2] = split_value[-2] + '2'
                                value = '_'.join(split_value)
                    else:
                        value = value.strip('*')
                else:
                    if col == 'INSTRUMENT_ID':
                        value = file('instrument_id')
                    elif col == 'INSTRUMENT_PROD':
                        value = pressure_instrument_info.get('INSTRUMENT_PROD', '')
                    elif col == 'INSTRUMENT_MOD':
                        value = pressure_instrument_info.get('INSTRUMENT_MOD', '')
                    elif col == 'INSTRUMENT_SERIE':
                        value = file('instrument_serie')
                    elif col == 'TIME':
                        value = file('date')
                row_list.append(value)
            self._data.append('\t'.join(row_list))

    def _add_header_information_to_cnv_info(self, cnv_file):
        names = cnv_file.get_reported_names()
        for name in names:
            cnv_code = name.split(':')[0].strip()
            info = {'parameter': cnv_code,
                    'serial_number': None}
            self.cnv_info.append(info)

    def _save_file(self, overwrite=False):
        if self._save_path.exists() and not overwrite:
            return 
        # if self._save_path.exists() and overwrite:
        #     os.remove(self._save_path)
        with open(self._save_path, 'w') as fid:
            fid.write('\n'.join(self._data))


class CreateSensorInfoSummaryFile:

    def __init__(self):
        self._paths = None
        self._sensor_info_items = {}

    def create_from_packages(self, packs, output_dir, **kwargs):
        self._paths = self._get_paths_from_packages(packs)
        self._save_info()
        self.write_summary_to_file(output_dir, **kwargs)

    @staticmethod
    def _get_paths_from_packages(packs):
        paths = []
        for pack in packs:
            path = pack.get_file_path(suffix='.sensorinfo')
            if not path:
                raise FileNotFoundError(f'No .sensorinfo file for package {pack.key}')
            paths.append(path)
        return paths

    def _save_info(self):
        self._sensor_info_items = {}
        for path in self._paths:
            header = None
            with open(path) as fid:
                for r, line in enumerate(fid):
                    split_line = [item.strip() for item in line.strip().split('\t')]
                    if r == 0:
                        header = split_line
                        continue
                    data = dict(zip(header, split_line))
                    key = SensorInfoItem.get_key(data)
                    par = key[1]
                    self._sensor_info_items.setdefault(par, [])
                    if not self._sensor_info_items[par] or self._sensor_info_items[par][-1]['key'] != key:
                        self._sensor_info_items[par].append(dict(key=key,
                                                                 obj=SensorInfoItem()))
                    self._sensor_info_items[par][-1]['obj'].add_data(data)

    def write_summary_to_file(self, directory, **kwargs):
        path = pathlib.Path(directory, 'sensorinfo.txt')
        if path.exists() and not kwargs.get('overwrite'):
            raise FileExistsError(path)
        columns = get_sensor_info_columns()
        lines = []
        lines.append('\t'.join(columns))
        for par in self._sensor_info_items.keys():
            for item in self._sensor_info_items[par]:
                info = item['obj'].get_info()
                lines.append('\t'.join([info.get(col, '') for col in columns]))

        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path

