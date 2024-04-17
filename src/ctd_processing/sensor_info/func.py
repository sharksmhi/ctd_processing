import pathlib

# from .instrument_file import InstrumentFile
# from .sensor_info_file import CreateSensorInfoFile


def get_sensor_info_columns():
    path = pathlib.Path(pathlib.Path(__file__).parent.parent, 'resources', 'sensor_info_columns.txt')
    columns = []
    with open(path) as fid:
        for line in fid:
            sline = line.strip()
            if not sline:
                continue
            columns.append(sline)
    return columns

