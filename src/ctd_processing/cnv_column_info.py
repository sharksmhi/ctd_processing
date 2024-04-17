from pathlib import Path

from ctd_processing import exceptions


class CnvSensorInfo(dict):
    def __init__(self, data, file_path):
        self._file_path = file_path
        for key, value in data.items():
            if key in ['active', 'index']:
                value = int(value)
            if key == 'active':
                value = bool(value)
            self[key] = value
            setattr(self, key, value)

    def __repr__(self):
        return_list = [f'CnvSensorInfo (dict): {self["parameter"]}']
        for key, value in self.items():
            return_list.append(f'    {key.ljust(10)}{value}')
        return '\n'.join(return_list)

    @property
    def name(self):
        return self['parameter']

    @property
    def file(self):
        return self._file_path.stem


class CnvInfoFile:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.file_stem = self.file_path.stem
        self.sensor_info = {}
        self._load_file()

    def __repr__(self):
        return f'CnvInfoFile: {self.file_stem}'

    def _load_file(self):
        with open(self.file_path) as fid:
            for i, line in enumerate(fid):
                line = line.strip()
                if not line:
                    continue
                split_line = [item.strip() for item in line.strip().split('\t')]
                if i == 0:
                    header = split_line
                else:
                    obj = CnvSensorInfo(dict(zip(header, split_line)), self.file_path)
                    self.sensor_info[obj['index']] = obj

    def get_info(self):
        return self.sensor_info


class CnvInfoFiles:
    def __init__(self, directory):
        self.directory = Path(directory)
        self._files = {}
        self._load_files()

    def __repr__(self):
        info = ['CnvInfoFiles'] + list(self._files)
        return '\n'.join(info)

    def _load_files(self):
        for file_path in self.directory.iterdir():
            self._files[file_path.stem] = CnvInfoFile(file_path)

    @property
    def files(self):
        return sorted(self._files)

    def get_info(self, ctd_nr):
        ctd_nr = str(ctd_nr)
        if ctd_nr not in self._files:
            raise exceptions.InvalidInstrumentSerialNumber
        return self._files.get(ctd_nr).get_info()


if __name__ == '__main__':
    f = CnvInfoFiles('cnv_column_info')