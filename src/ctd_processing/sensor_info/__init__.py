import pathlib
from .func import get_sensor_info_columns

from .instrument_file import InstrumentFile
from .sensor_info_file import CreateSensorInfoFile
from .sensor_info_file import CreateSensorInfoSummaryFile

import logging

logger = logging.getLogger(__name__)


def create_sensor_info_files_from_cnv_files_in_directory(directory, instrument_file_path, output_dir=None, **kwargs):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in pathlib.Path(directory).iterdir():
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path, output_dir=output_dir, **kwargs)


def create_sensor_info_files_from_cnv_files(cnv_files, instrument_file_path, **kwargs):
    sensor_info = get_sensor_info_object(instrument_file_path)
    for path in cnv_files:
        if not path.suffix == '.cnv':
            continue
        sensor_info.create_file_from_cnv_file(path, **kwargs)


def create_sensor_info_files_from_package(pack, instrument_file_path, **kwargs):
    cnv = pack.get_file_path(suffix='.cnv', prefix=None)
    if not cnv:
        FileNotFoundError(f'Could not find cnv file for package: {pack.key}')
    create_sensor_info_files_from_cnv_files([cnv], instrument_file_path, **kwargs)


def get_sensor_info_object(instrumentinfo_file):
    if isinstance(instrumentinfo_file, InstrumentFile):
        inst_file = instrumentinfo_file
    else:
        inst_file = InstrumentFile(instrumentinfo_file)
    sensor_info = CreateSensorInfoFile(inst_file)
    return sensor_info


def create_sensor_info_summary_file_from_packages(packs, output_dir=None, **kwargs):
    sensorinfo = CreateSensorInfoSummaryFile()
    return sensorinfo.create_from_packages(packs, output_dir=output_dir, **kwargs)