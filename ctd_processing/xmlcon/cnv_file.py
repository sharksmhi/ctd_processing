import pathlib
import datetime
import xml.etree.ElementTree as ET


class CNVfileXML:

    def __init__(self, file_path):
        self.path = pathlib.Path(file_path)
        lines = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        is_xml = False
        with open(file_path) as fid:
            for line in fid:
                if line.startswith('# <Sensors count'):
                    is_xml = True
                if is_xml:
                    lines.append(line[2:])
                if line.startswith('# </Sensors>'):
                    break
        self.xmlstring = ''.join(lines)
        self.tree = ET.ElementTree(ET.fromstring(self.xmlstring))

    def get_sensor_info(self):
        index = {}
        sensor_list = []
        for i, sensor in enumerate(self.tree.findall('sensor')):
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
        # for par, index_list in index.items():
        #     if len(index_list) == 1:
        #         continue
        #     for nr, i in enumerate(index_list):
        #         sensor_list[i]['parameter'] = f'{sensor_list[i]["parameter"]}_{nr+1}'
        return sensor_list

    def _get_comment_for_channel(self, channel):
        channel_str = f'Channel="{channel}"'
        xml_lines = self.xmlstring.split('\n')
        for row1, row2 in zip(xml_lines[:-1], xml_lines[1:]):
            if channel_str not in row1:
                continue
            comment = row2.split(',', 1)[-1][:-4].strip()
            return comment

    @staticmethod
    def get_datetime_object(date_str):
        if len(date_str) == 8:
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

    @property
    def serial_number(self):
        for sensor in self.get_sensor_info():
            if sensor['parameter'] == 'PressureSensor':
                return sensor['serial_number']


def get_sensor_info(file_path):
    return CNVfileXML(file_path).get_sensor_info()


def get_parameter_list(file_path):
    obj = CNVfileXML(file_path)
    sensor_info = obj.get_sensor_info()
    return [(info['internal_parameter'], info['parameter']) for info in sensor_info]