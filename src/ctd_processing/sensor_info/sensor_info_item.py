import datetime

from .func import get_sensor_info_columns


class SensorInfoItem:
    """
    Holds information about a sensor INSTRUMENT_SERIE - PARAM_REPORTED combination.
    """
    def __init__(self):
        # self._all_columns = func.get_sensor_info_columns()
        self._all_columns = get_sensor_info_columns()
        self._columns = [col for col in self._all_columns if col not in ['VALIDFR', 'VALIDTO']]
        self._key = ()
        self._data = {}
        self._valid_from = None
        self._valid_to = None
        self._calibration_dates = set()

    def _check_columns(self, data):
        if not all([col in self._columns for col in data.keys()]):
            raise Exception('Invalid data to SensorInfoItem')

    @staticmethod
    def get_key(data):
        return (data['SENSOR_ID'], data['PARAM'])

    @staticmethod
    def _get_time_object(time_string):
        return datetime.datetime.strptime(time_string, '%Y-%m-%d')

    @staticmethod
    def _get_time_string(datetime_object):
        return datetime_object.strftime('%Y-%m-%d')

    @property
    def valid_from(self):
        return self._valid_from

    @property
    def valid_to(self):
        return self._valid_to

    def add_data(self, data):
        self._check_columns(data)
        if not self._key:
            self._add_first_data(data)
        else:
            return self._add_additional_data(data)
        return self._key

    def _add_first_data(self, data):
        self._key = self.get_key(data)
        self._data = data
        self._add_info(data)

    def _add_additional_data(self, data):
        if self.get_key(data) != self._key:
            return False
        self._add_info(data)
        return self._key

    def _add_info(self, data):
        self._set_valid_from(data)
        self._set_valid_to(data)
        self._add_calibration_date(data)

    def _set_valid_from(self, data):
        if not self._valid_from:
            self._valid_from = self._get_time_object(data['TIME'])
        else:
            self._valid_from = min(self._valid_from, self._get_time_object(data['TIME']))

    def _set_valid_to(self, data):
        if not self._valid_to:
            self._valid_to = self._get_time_object(data['TIME'])
        else:
            self._valid_to = max(self._valid_to, self._get_time_object(data['TIME']))

    def _add_calibration_date(self, data):
        self._calibration_dates.add(data['CALIB_DATE'])

    def get_info(self):
        info = self._data.copy()
        info['VALIDFR'] = self._valid_from.strftime('%Y-%m-%d')
        info['VALIDTO'] = self._valid_to.strftime('%Y-%m-%d')
        info['CALIB_DATE'] = ', '.join(sorted(self._calibration_dates))
        return info