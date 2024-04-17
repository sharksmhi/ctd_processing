import datetime
import time
import logging

from file_explorer import patterns
from file_explorer.seabird import xmlcon_parser
from file_explorer.seabird.cnv_file import CnvFile
from file_explorer.seabird import edit_cnv

from file_explorer.seabird.utils import get_header_form_information

from ctd_processing import utils

from ctd_processing.value_format import ValueFormat

logger = logging.getLogger(__file__)


class InvalidFileToModify(Exception):
    pass


class HeaderName:
    _string = None
    _index = None
    _code = None
    _parameter = None
    _description = None

    def __init__(self, string):
        self._string = string.strip()
        self._save_info()

    def __str__(self):
        return self._string

    def __repr__(self):
        return self.__str__()

    def _save_info(self):
        split_line = self._string.split('=', 1)
        self._index = int(split_line[0].strip().split()[-1])
        split_par = split_line[1].split(':')
        self._code = split_par[0].strip()
        self._parameter = split_par[1].strip()
        self._description = split_line[-1].strip()

    @property
    def index(self):
        return self._index

    @property
    def code(self):
        return self._code

    @property
    def parameter(self):
        return self._parameter

    @property
    def description(self):
        return self._description


class Header:
    def __init__(self, linebreak='\n'):
        self.linebreak = linebreak
        self._lines = []

    @property
    def lines(self):
        return self._lines

    def add_line(self, row):
        self._lines.append(row.strip())

    @staticmethod
    def old_insert_row_after(rows, row, after_str, ignore_if_string=None):
        for line in rows:
            if row == line:
                return
        for i, value in enumerate(rows[:]):
            if after_str in value:
                if ignore_if_string and ignore_if_string in rows[i + 1]:
                    continue
                rows.insert(i + 1, row.strip())
                break

    @staticmethod
    def insert_row_after(lines, row, after_str):
        for line in lines:
            if row == line:
                return
        for i, value in enumerate(lines[:]):
            if after_str in value:
                lines.insert(i + 1, row.strip())
                break

    @staticmethod
    def append_to_row(lines, string_in_row, append_string):
        for i, value in enumerate(lines[:]):
            if string_in_row in value:
                if value.endswith(append_string):
                    continue
                new_string = lines[i] + append_string.rstrip()
                # if self._rows[i] == new_string:
                #     continue
                lines[i] = new_string
                break

    @staticmethod
    def get_row_index_for_matching_string(lines, match_string, as_list=False, ignore_case=False):
        index = []
        for i, value in enumerate(lines):
            if ignore_case:
                if match_string.lower() in value.lower():
                    index.append(i)
            else:
                if match_string in value:
                    index.append(i)
        if not index:
            return None
        if as_list:
            return index
        if len(index) == 1:
            return index[0]
        return index

    @staticmethod
    def replace_string_at_index(lines, index, from_string, to_string, ignore_if_present=True):
        if index is None:
            return
        if type(index) == int:
            index = [index]
        for i in index:
            if to_string in lines[i] and ignore_if_present:
                continue
            lines[i] = lines[i].replace(from_string, to_string)

    @staticmethod
    def replace_row(lines, index, new_value):
        lines[index] = new_value.strip()


class Parameter:
    def __init__(self, use_value_format=False, value_format=None, index=None, name=None, description=None, **kwargs):
    # def __init__(self, use_cnv_info_format=False, cnv_info_object=None, index=None, name=None, **kwargs):

        self.info = {'index': index,
                     'name': name,
                     'description': description}
        self.info.update(kwargs)

        # self.use_cnv_info_format = use_cnv_info_format
        # self.cnv_info_object = cnv_info_object
        self.use_value_format = use_value_format
        self.value_format = value_format
        self._tot_value_length = 11
        self._value_format = 'd'
        self._nr_decimals = None
        self.sample_value = None
        self._data = []
        self.active = True

    def __getitem__(self, item):
        return self.info.get(item)

    def __getattr__(self, item):
        return self.info.get(item)

    def __repr__(self):
        return_list = [f'CNVparameter (dict): {self.info["name"]}']
        blanks = ' '*4
        for key, value in self.info.items():
            return_list.append(f'{blanks}{key:<20}{value}')

        if len(self._data):
            return_list.append(f'{blanks}{"Sample value":<20}{self.sample_value}')
            if self.use_cnv_info_format:
                form = f'{self.get_format()} (from info file)'
            else:
                form = f'{self.get_format()} (calculated from data)'
            return_list.append(f'{blanks}{"Value format":<20}{form}')
        return '\n'.join(return_list)

    def _set_nr_decimals(self, value_str):
        # Keeps the highest number och decimals in self._nr_decimals
        # Also saves sample_value
        if self._nr_decimals is None:
            self._nr_decimals = len(value_str.strip().split('e')[0].split('.')[-1])
            self.sample_value = float(value_str)
        else:
            nr = len(value_str.strip().split('e')[0].split('.')[-1])
            if nr > self._nr_decimals:
                self._nr_decimals = nr
                self.sample_value = float(value_str)

    def get_format(self, value=None):
        if self.use_value_format:
            # print('--', self.name, self.value_format(self.description))
            return self.value_format(self.description)
        if self._nr_decimals is None:
            form = f'{self._tot_value_length}{self._value_format}'
        else:
            if value and self._value_format == 'e' and str(value).startswith('-'):
                form = f'{self._tot_value_length}.{self._nr_decimals - 1}{self._value_format}'
            else:
                form = f'{self._tot_value_length}.{self._nr_decimals}{self._value_format}'
        return form

    def set_value_length(self, length):
        self._tot_value_length = length

    def add_data(self, value_str):
        string = value_str.strip('+-')
        if '+' in string or '-' in string:
            self._value_format = 'e'
        elif '.' in value_str:
            self._value_format = 'f'
        if '.' in value_str:
            self._set_nr_decimals(value_str)
            value = float(value_str)
        else:
            value = int(value_str)
            self._value_format = 'd'

        self._data.append(value)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def change_name(self, new_name):
        self.info['name'] = new_name

    def get_value_as_string_for_index(self, index):
        if type(self.data[index]) == str:
            return self.data[index].rjust(self._tot_value_length)
        return '{:{}}'.format(self.data[index], self.get_format(self.data[index]))

    def set_active(self, is_active):
        self.active = is_active


class ModifyCnv(CnvFile):
    missing_value = -9.990e-29
    missing_value_str = '-9.990e-29'
    g = 9.818  # g vid 60 gr nord (dblg)

    def __init__(self, *args, **kwargs):
        self._station = kwargs.pop('station', None)
        self._use_value_format = kwargs.pop('use_value_format', True)
        self._value_format_object = ValueFormat(value_format_path=kwargs.pop('value_format_path', None))
        super().__init__(*args, **kwargs)

    def modify(self):
        self._validate()
        self._modify()

    def _validate(self):
        if not (self('suffix') == '.cnv' and self('prefix') == 'd'):
            raise InvalidFileToModify

    def _modify(self):
        self._save_columns()
        # self._check_index()
        self._header_lines = self.header.lines[:]
        # self._data_lines = self.data_lines[:]

        self._modify_header_information()
        self._modify_irradiance()
        self._modify_fluorescence()
        self._modify_depth()
        self._modify_station()

        self._set_lines()

    def _save_info_from_file(self):
        self._header_form = {'info': []}
        self._header_names = []
        self._nr_data_lines = 0
        self.header = Header()
        self._parameters = {}
        self._header_cruise_info = {}

        self.xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        print('print(len(self.xml_lines))', len(self.xml_lines))
        is_xml = False

        header = True
        has_set_value_length = False
        with open(self.path) as fid:
            for line in fid:
                strip_line = line.strip()

                # General header info
                if line.startswith('* System UTC'):
                    self._header_datetime = datetime.datetime.strptime(line.split('=')[1].strip(), self.header_date_format)
                elif line.startswith('* NMEA Latitude'):
                    print(self.path)
                    self._header_lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('* NMEA Longitude'):
                    self._header_lon = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Station'):
                    self._header_station = line.split(':')[-1].strip()
                elif line.startswith('** Cruise'):
                    self._header_cruise_info = patterns.get_cruise_match_dict(line.split(':')[-1].strip())

                # Header form
                if line.startswith('**'):
                    if line.count(':') == 1:
                        key, value = [part.strip() for part in line.strip().strip('*').split(':')]
                        self._header_form[key] = value
                    else:
                        self._header_form['info'].append(strip_line)

                # Parameters
                elif strip_line.startswith('# name'):
                    hn = HeaderName(line)
                    self._header_names.append(hn)
                    obj = Parameter(use_value_format=self._use_value_format,
                                    value_format=self._value_format_object,
                                    index=hn.index,
                                    name=hn.parameter,
                                    description=hn.description)
                    # obj = Parameter(use_cnv_info_format=False,
                    #                 cnv_info_object=None,
                    #                 index=hn.index, name=hn.parameter)
                    self._parameters[obj.index] = obj

                # XML
                if line.startswith('# <Sensors count'):
                    is_xml = True
                if is_xml:
                    self.xml_lines.append(line[2:])
                if line.startswith('# </Sensors>'):
                    is_xml = False
                    self._xml_tree = xmlcon_parser.get_parser_from_string(''.join(self.xml_lines))
                    self._sensor_info = xmlcon_parser.get_sensor_info(self._xml_tree)

                if '*END*' in line:
                    self.header.add_line(line)
                    header = False
                    continue
                if header:
                    self.header.add_line(line)
                else:
                    if not line.strip():
                        continue
                    self._nr_data_lines += 1
                    split_line = strip_line.split()
                    if not has_set_value_length:
                        tot_len = len(line.rstrip())
                        value_length = tot_len / len(split_line)
                        int_value_lenght = int(value_length)
                        if int_value_lenght != value_length:
                            print(self.path)
                            raise ValueError('Something is wrong in the file!')
                        for i, value in enumerate(split_line):
                            self._parameters[i].set_value_length(int_value_lenght)
                        has_set_value_length = True
                    for i, value in enumerate(split_line):
                        self._parameters[i].add_data(value)

    def get_sensor_info(self):
        index = {}
        sensor_list = []
        for i, sensor in enumerate(self._xml_tree.findall('sensor')):
            child_list = sensor.getchildren()
            if not child_list:
                continue
            child = child_list[0]
            par = child.tag
            nr = child.find('SerialNumber').text
            calibration_date = child.find('CalibrationDate').text
            if calibration_date:
                # print('calibration_date', calibration_date, par)
                calibration_date = self.get_datetime_object(calibration_date)
            if nr is None:
                nr = ''
            index.setdefault(par, [])
            index[par].append(i)
            channel = int(sensor.attrib['Channel'])
            data = {'channel': channel,
                    'internal_parameter': par,
                    'serial_number': nr,
                    'calibration_date': calibration_date,
                    'parameter': self._get_comment_for_channel(channel)}
            sensor_list.append(data)
        return sensor_list

    @staticmethod
    def get_datetime_object(date_str):
        if len(date_str) == 6:
            format_str = '%d%m%y'
        elif len(date_str) == 8 and '-' not in date_str:
            format_str = '%d%m%Y'
        else:
            if '-' in date_str:
                parts = date_str.split('-')
            else:
                parts = date_str.split(' ')
            if len(parts[-1]) == 2:
                format_str = '%d-%b-%y'
            else:
                format_str = '%d-%b-%Y'
            date_str = '-'.join(parts)
        return datetime.datetime.strptime(date_str, format_str)

    def _get_comment_for_channel(self, channel):
        channel_str = f'Channel="{channel}"'
        for row1, row2 in zip(self.xml_lines[:-1], self.xml_lines[1:]):
            if channel_str not in row1:
                continue
            comment = row2.split(',', 1)[-1][:-4].strip()
            return comment

    def _save_columns(self):
        self.col_pres = None
        self.col_dens = None
        self.col_dens2 = None
        self.col_depth = None
        self.col_sv = None

        for par in self._parameters.values():
            if 'Pressure, Digiquartz [db]' in par.name:
                self.col_pres = par.index
            elif 'Density [sigma-t' in par.name:
                self.col_dens = par.index
            elif 'Density, 2 [sigma-t' in par.name:
                self.col_dens2 = par.index
            elif 'Depth [fresh water, m]' in par.name:
                self.col_depth = par.index
            elif 'Depth [true depth, m]' in par.name:
                self.col_depth = par.index
            elif 'Sound Velocity [Chen-Millero, m/s]' in par.name:
                self.col_sv = par.index

    @property
    def parameters(self):
        return self._parameters

    @property
    def pressure_data(self):
        return self._parameters[self.col_pres].data

    @property
    def depth_data(self):
        return self._parameters[self.col_depth].data

    @property
    def sound_velocity_data(self):
        return self._parameters[self.col_sv].data

    @property
    def density_data(self):
        if self._parameters[self.col_dens].active:
            return self._parameters[self.col_dens].data
        elif self._parameters[self.col_dens2].active:
            return self._parameters[self.col_dens2].data
        else:
            return [ModifyCnv.missing_value]*self._nr_data_lines

    @property
    def header_lines(self):
        return self.header.lines

    @property
    def data_lines(self):
        data_rows = []
        for r in range(self._nr_data_lines):
            line_list = []
            for par, obj in self.parameters.items():
                value = obj.get_value_as_string_for_index(r)
                line_list.append(value)
            line_string = ''.join(line_list)
            data_rows.append(line_string)
        return data_rows

    @property
    def sensor_info(self):
        return self._sensor_info

    def string_match_header_form(self, string):
        for value in self._header_form.values():
            if isinstance(value, list):
                for item in value:
                    if string in item:
                        return True
            else:
                if string in value:
                    return True
        return False

    def get_parameter_channels_and_names(self):
        info = {}
        for head in self._header_names:
            info[head.index] = head.parameter
        return info

    def get_sensor_id_and_parameter_mapping(self):
        header_name_info = self.get_parameter_channels_and_names()
        mapping = {}
        for info in self.sensor_info:
            mapping[info['serial_number']] = header_name_info.get(info['channel'], '')
        return mapping

    def get_reported_names(self):
        names = []
        for head in self._header_names:
            names.append(head.description)
        # return sorted(names)
        return names

    def _set_lines(self):
        all_lines = []
        all_lines.extend(self._header_lines)
        all_lines.extend(self.data_lines[:])
        all_lines.append('')

        self.lines = all_lines

    def _modify_header_information(self):
        svMean = self._get_mean_sound_velocity()
        now = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        after_str = '** Ship'
        rows_to_insert = [f'** Average sound velocity: {str("%6.2f" % svMean)} m/s',
                          f'** True-depth calculation: {now}',
                          # f'** CTD Python Module SMHI /ver 3-12/ feb 2012',
                          # f'** Python Module: ctd_processing, nov 2020'
                          # f'** LIMS Job: {self.year}{self.ctry}{self.ship}-{self.serie}'
                          ]
        for row in rows_to_insert:
            if 'True-depth calculation' in row:
                if self.string_match_header_form('True-depth calculation'):
                    continue
                Header.insert_row_after(self._header_lines, row, after_str)
            else:
                Header.insert_row_after(self._header_lines, row, after_str)
            after_str = row

    def _modify_irradiance(self):
        Header.append_to_row(self._header_lines, 'par: PAR/Irradiance', ' [µE/(cm^2*s)]')

    def _modify_fluorescence(self):
        # Lägger till Chl-a på de fluorometrar som har beteckning som börjar på FLNTURT
        par_name_1 = self._get_parameter_name_matching_string('Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]')
        fluo_index_1 = Header.get_row_index_for_matching_string(self._header_lines,
                                                                'Fluorescence, WET Labs ECO-AFL/FL [mg/m^3]')
        fluo_xml_index_1 = Header.get_row_index_for_matching_string(self._header_lines,
                                                                    'Fluorometer, WET Labs ECO-AFL/FL -->')
        serial_index_1 = Header.get_row_index_for_matching_string(self._header_lines, '<SerialNumber>FLNTURT',
                                                                  as_list=True)

        par_name_2 = self._get_parameter_name_matching_string('Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]')
        fluo_index_2 = Header.get_row_index_for_matching_string(self._header_lines,
                                                                'Fluorescence, WET Labs ECO-AFL/FL, 2 [mg/m^3]')
        fluo_xml_index_2 = Header.get_row_index_for_matching_string(self._header_lines,
                                                                    'Fluorometer, WET Labs ECO-AFL/FL, 2 -->')
        serial_index_2 = Header.get_row_index_for_matching_string(self._header_lines, '<SerialNumber>FLPCRTD',
                                                                  as_list=True)

        if fluo_xml_index_1 and (fluo_xml_index_1 + 2) in serial_index_1:
            Header.replace_string_at_index(self._header_lines, fluo_xml_index_1, 'Fluorometer', 'Chl-a Fluorometer')
            Header.replace_string_at_index(self._header_lines, fluo_index_1, 'Fluorescence', 'Chl-a Fluorescence')
            new_par_name_1 = par_name_1.replace('Fluorescence', 'Chl-a Fluorescence')
            self._change_parameter_name(par_name_1, new_par_name_1)

        if fluo_xml_index_2 and (fluo_xml_index_2 + 2) in serial_index_2:
            if not par_name_2:
                raise Exception(
                    f'Fluorometer parameter finns i xml-delen ({fluo_xml_index_2}) men inte i parameterlistan. Kan vara missmatch mellan DataCnv och xmlcon: \n{self.path}')
            Header.replace_string_at_index(self._header_lines, fluo_xml_index_2, 'Fluorometer',
                                           'Phycocyanin Fluorometer')
            Header.replace_string_at_index(self._header_lines, fluo_index_2, 'Fluorescence', 'Phycocyanin Fluorescence')
            new_par_name_2 = par_name_2.replace('Fluorescence', 'Phycocyanin Fluorescence')
            self._change_parameter_name(par_name_2, new_par_name_2)

    def _modify_depth(self):
        index = Header.get_row_index_for_matching_string(self._header_lines, 'depFM: Depth [fresh water, m]')
        Header.replace_string_at_index(self._header_lines, index, 'fresh water', 'true depth')
        par_name = self._get_parameter_name_matching_string('depFM: Depth [fresh water, m]')
        if par_name:
            new_par_name = par_name.replace('fresh water', 'true depth')
            self._change_parameter_name(par_name, new_par_name)

        span_depth_index = Header.get_row_index_for_matching_string(self._header_lines,
                                                                    f'# span {self.col_depth}')
        true_depth_values = self._get_calculated_true_depth()
        if int(self.col_depth) < 10:
            new_line = '# span %s =%11.3f,%11.3f%7s' % (
            self.col_depth, min(true_depth_values), max(true_depth_values), '')
        else:
            new_line = '# span %s =%11.3f,%11.3f%6s' % (
            self.col_depth, min(true_depth_values), max(true_depth_values), '')
        Header.replace_row(self._header_lines, span_depth_index, new_line)

        # Ersätt data i fresh water kolumnen med true depth avrundar true depth till tre decimaler
        new_depth_data = []
        for value in true_depth_values:
            if value == self.missing_value:
                new_depth_data.append(self.missing_value_str)
                # new_depth_data.append(self.missing_value)
            else:
                new_depth_data.append(round(value, 3))
        self.parameters[self.col_depth].data = new_depth_data

    def _modify_station(self):
        logger.debug(f'_modify_station: {self._station}')
        if not self._station:
            return
        if self._station == self._header_station:
            logger.info(f'Given station "{self._header_station}" name is ths same as in header in file: {self.path}')
            return
        index = Header.get_row_index_for_matching_string(self._header_lines, 'station', ignore_case=True)
        Header.replace_string_at_index(self._header_lines, index, self._header_station, self._station,
                                       ignore_if_present=False)
        logger.error(f'{self._header_lines[index]=}')

    def _get_mean_sound_velocity(self):
        svCM_data = self.sound_velocity_data
        return sum(svCM_data) / len(svCM_data)

    def _get_parameter_name_matching_string(self, match_string):
        for par in self.parameters.values():
            if match_string in par.name:
                return par.name

    def _change_parameter_name(self, current_name, new_name):
        for par in self.parameters.values():
            if par.name == new_name:
                return
        for par in self.parameters.values():
            if current_name == par.name:
                par.change_name(new_name)

    def _get_calculated_true_depth(self):
        prdM_data = self.pressure_data
        sigT_data = self.density_data

        # Beräkning av truedepth # Ersätt depFM med true depth i headern
        # Start params
        dens_0 = (sigT_data[0] + 1000.) / 1000.  # ' start densitet
        p_0 = 0
        depth = 0
        true_depth = []
        for q in range(len(prdM_data)):
            if sigT_data[q] != self.missing_value:
                # decibar till bar (dblRPres)
                rpres = prdM_data[q] * 10.
                # Beräknar densitet (dblDens)
                dens = (sigT_data[q] + 1000.) / 1000.
                # Beräknar delta djup (dblDDjup)
                ddepth = (rpres - p_0) / ((dens + dens_0) / 2. * self.g)
                # Summerar alla djup och använd framräknande trycket i nästa loop
                # Om det är första (ej helt relevant kanske) eller sista värdet dela med två enl. trappetsmetoden
                dens_0 = dens
                #    if q == 0 or q == (len(prdM)-1):
                #        Depth = Depth + DDepth / 2.
                #    else:
                #        Depth = Depth + DDepth
                # Ändrad av Örjan 2015-02-10 /2. första och sista djupet borttaget.
                depth = depth + ddepth
                # Spara framräknat djup för nästa loop
                p_0 = rpres
                # Sparar undan TrueDepth
                true_depth.append(depth)
            else:
                true_depth.append(self.missing_value)
        return true_depth

    # def _check_index(self):
    #     if not self.cnv_info_object:
    #         raise exceptions.MissingAttribute('cnv_info_object')
    #     for info, cnv in zip(self.cnv_info_object.values(), self.parameters.values()):
    #         if 'depFM: Depth [true depth, m], lat' in info.name:
    #             continue
    #         if info.name not in cnv.name:
    #             print(info.name)
    #             print(cnv.name)
    #             raise exceptions.InvalidParameterIndex(f'Index stämmer inte i cnv för parameter: {info.name}')
    #         cnv.active = True

    # def _set_active_parameters(self):
    #     for i, info in self.cnv_info_object.items():
    #         if i not in self.parameters:
    #             raise Exception(f'''Sensoruppsättningen stämmer inte!
    #                                Kontrollera sensoruppsättningen i fil:
    #                                ctd_processing/ctd_processing/ctd_files/seabird/cnv_column_info/{info.file}''')
    #         if info.name not in self.parameters[i].name:
    #             if 'Depth' not in info.name:
    #                 raise Exception(f'''Sensoruppsättningen stämmer inte!
    #                                 Det är kan vara för få eller får många sensorer beskrivna i fil:
    #                                 "ctd_processing/ctd_processing/ctd_files/seabird/cnv_column_info/{info.file}"
    #
    #                                 Index:             {i}
    #                                 Sensoruppsättning: {info.name}
    #                                 Info i fil:        {self.parameters[i].name}''')
    #         self.parameters[i].set_active(info.active)


def modify_cnv_down_file(package, directory=None, overwrite=False):
    file = ModifyCnv(package.get_file(prefix='d', suffix='.cnv').path, station=package('station', pref_suffix='.hdr'))
    file.key = package.key
    try:
        file.modify()
        target_path = file.save_file(directory, overwrite=overwrite)
        edit_cnv.add_lims_job(target_path, overwrite=True)
        return file
    except InvalidFileToModify:
        logger.warning(f'Invalid file to modify {file}')
    except Exception:
        raise



def get_parameter_channels_and_names_from_cnv(path):
    info = {}
    with open(path) as fid:
        for line in fid:
            if not line.startswith('# name'):
                continue
            name, par = line.split('=', 1)
            par = par.strip()
            channel = int(name.strip().split()[-1])
            info[channel] = par
    return info


def get_sensor_id_and_parameter_mapping_from_cnv(path):
    cnv_file = CnvFile(path)
    xml_info = cnv_file('sensor_info')
    # xml_info = xmlcon.CNVfileXML(path).get_sensor_info()
    name_info = get_parameter_channels_and_names_from_cnv(path)
    mapping = {}
    for info in xml_info:
        mapping[info['serial_number']] = name_info.get(info['channel'], '')
    return mapping


def get_reported_names_in_cnv(path):
    name_info = get_parameter_channels_and_names_from_cnv(path)
    return list(name_info.values())


# def get_header_form_information(path):
#     info = {}
#     with open(path) as fid:
#         for line in fid:
#             if not line.startswith('**'):
#                 continue
#             split_line = [part.strip() for part in line.strip('*').split(':', 1)]
#             if len(split_line) != 2:
#                 continue
#             info[split_line[0]] = split_line[1]
#             # Special treatment for metadata
#             if 'metadata' in split_line[0].lower():
#                 metadata = utils.metadata_string_to_dict(split_line[1])
#                 for key, value in metadata.items():
#                     info[key] = value
#     return info