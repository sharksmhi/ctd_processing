from pathlib import Path


class Parameter:

    def __init__(self, info):
        self._info = info

    @property
    def active(self):
        return self._info.get('active')

    @property
    def format(self):
        return self._info.get('format')

    @property
    def name(self):
        return self._info.get('parameter')


class ValueFormat:
    _parameters = None

    def __init__(self, value_format_path=None):
        if value_format_path:
            self._path = Path(value_format_path)
        else:
            self._path = Path(Path(__file__).parent, 'resources', 'value_format.txt')
        self._load_file()

    def __call__(self, parameter):
        """
        Returns the format matching parameter.
        First check for absolute match between parameter and key.
        If format not found we'll check if key in parameter
        """
        par = self._parameters.get(parameter)
        if not par:
            for key, p in self._parameters.items():
                if key.lower() in parameter.lower():
                    par = p
                    break
        if not par:
            raise Exception(f'No format found for parameter: {parameter}')
        return par.format

    def _load_file(self):
        self._parameters = {}
        header = None
        with open(self._path, encoding='cp1252') as fid:
            for line in fid:
                strip_line = line.strip()
                if not strip_line:
                    continue
                if line.startswith('#'):
                    continue
                split_line = [item.strip() for item in strip_line.split('\t')]
                if not header:
                    header = split_line
                    continue
                par = Parameter(dict(zip(header, split_line)))
                self._parameters[par.name] = par

