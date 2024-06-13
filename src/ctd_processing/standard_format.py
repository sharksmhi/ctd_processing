import codecs
import datetime
import logging
import os
import pathlib
import shutil

import file_explorer
from ctd_processing import exceptions
from ctd_processing.delivery_note import CreateDeliveryNote
from ctd_processing.metadata import CreateMetadataFile
from ctd_processing.sensor_info import create_sensor_info_files_from_cnv_files
from ctd_processing.sensor_info.sensor_info_file import CreateSensorInfoSummaryFile
from ctdpy.core import session as ctdpy_session

logger = logging.getLogger(__file__)


class StandardFormatComments:
    def __init__(self, file_path):
        self._path = pathlib.Path(file_path)
        self._info = {}
        self._automatic_qc = []

    def save_comment_info(self):
        self._info = {}
        with codecs.open(self._path, encoding='cp1252') as fid:
            for r, line in enumerate(fid):
                sline = line.strip()
                if line.startswith('//'):
                    if r <= 2:
                        continue
                    self._save_comment_line(sline)
                else:
                    return

    def _save_comment_line(self, sline):
        text = sline.strip('/')
        split_text = text.split(';', 2)
        self._info.setdefault(split_text[0], {})
        if len(split_text) == 3:
            self._info[split_text[0]][split_text[1]] = split_text[2]
            date = self._automatic_qc_datetime_from_comment_line(sline)
            if date:
                self._automatic_qc.append(date)
        elif split_text[1].startswith('#'):
            self._info[split_text[0]].setdefault('from_cnv', [])
            self._info[split_text[0]]['from_cnv'].append(split_text[1])

    def _automatic_qc_matches_today(self):
        # Finds the information in self._automatic_qc
        for dtime in self._automatic_qc:
            if dtime.date() == datetime.datetime.today().date():
                return True
        return False

    def has_automatic_qc_today(self):
        if self._info:
            return self._automatic_qc_matches_today()
        else:
            with open(self._path) as fid:
                for line in fid:
                    if not line.startswith('//'):
                        return False
                    if not line.startswith('//COMNT_QC; AUTOMATIC QC'):
                        continue
                    date = self._automatic_qc_date_from_comment_line(line)
                    if date == datetime.datetime.today().date():
                        return True
                return False

    @staticmethod
    def _automatic_qc_datetime_from_comment_line(line):
        if not line.startswith('//COMNT_QC; AUTOMATIC QC'):
            return
        split_line = line.split(';')
        time_str = split_line[2].split()[-1]
        dtime = datetime.datetime.strptime(time_str, '%Y%m%d%H%M')
        return dtime

    @staticmethod
    def _automatic_qc_date_from_comment_line(line):
        dtime = StandardFormatComments._automatic_qc_datetime_from_comment_line(line)
        if not dtime:
            return
        return dtime.date()

    @property
    def info_tags(self):
        return sorted(self._info)

    def get_automatic_qc_datetimes(self):
        return self._automatic_qc


class old_CreateStandardFormat:

    def __init__(self, paths_object):
        self.paths = paths_object
        self._cnv_files = []
        self._overwrite = False
        self._metadata_path = None
        self._export_directory = None
        self._output_dir = None

        self._sensorinfo_file_path = None
        self._metadata_file_path = None

        # self.delivery_metadata_file_path = None

    def create_files_from_cnv(self, cnv_file_list, overwrite=False, **kwargs):
        if not cnv_file_list:
            return

        self._output_dir = pathlib.Path(self.paths.get_local_directory('temp'), 'delivery_files', datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        if not self._output_dir.exists():
            os.makedirs(self._output_dir)

        # self.delivery_metadata_file_path = pathlib.Path(self._output_dir, 'ctd_metadata.xlsx')

        self._cnv_files = cnv_file_list
        self._overwrite = bool(overwrite)

        self._create_sensorinfo_file()
        self._create_metadata_file(**kwargs)
        self._create_deliverynote_file(**kwargs)
        self._create_standard_format_files()
        self._copy_standard_format_files_to_local()

    def _create_sensorinfo_file(self):
        create_sensor_info_files_from_cnv_files(self._cnv_files,
                                                self.paths.get_path('instrumentinfo_file'),
                                                output_dir=self._output_dir)
        sensorinfo = CreateSensorInfoSummaryFile(self._output_dir)
        self._sensorinfo_file_path = sensorinfo.write_summary_to_file()

    def _create_metadata_file(self, **kwargs):
        metadata = CreateMetadataFile(file_list=self._cnv_files, **kwargs)
        self._metadata_file_path = metadata.write_to_file(self._output_dir)

    def _create_deliverynote_file(self, **kwargs):
        delivery = CreateDeliveryNote(file_list=self._cnv_files,
                                      **kwargs,
                                      )
        self._deliverynote_file_path = delivery.write_to_file(self._output_dir)

    def _create_standard_format_files(self):
        all_file_paths = self._cnv_files + [self._sensorinfo_file_path, self._metadata_file_path, self._deliverynote_file_path]
        s = ctdpy_session.Session(filepaths=all_file_paths,
                                  reader='smhi')
        datasets = s.read()

        data_path = s.save_data(datasets,
                                writer='ctd_standard_template',
                                keep_original_file_names=True,
                                return_data_path=True)
        
        self._export_directory = pathlib.Path(data_path)

    def _copy_standard_format_files_to_local(self):
        target_dir = self.paths.get_local_directory('data', create=True)
        cnv_file_stems = [path.stem for path in self._cnv_files]

        for source_path in self._export_directory.iterdir():
            if source_path.stem not in cnv_file_stems:
                continue
            target_path = pathlib.Path(target_dir, source_path.name)
            if target_path.exists() and not self._overwrite:
                raise exceptions.FileExists(target_path)
            shutil.copy2(source_path, target_path)


class CreateStandardFormat:
    def __init__(self, file_handler, **kwargs):
        self._file_handler = file_handler
        self._pack = None
        self._kwargs = kwargs

        self._temp_dir = None

        self._sensorinfo_file_path = None
        self._metadata_file_path = None
        self._deliverynote_file_path = None

    def _set_pack(self, pack):
        if not isinstance(pack, file_explorer.Package):
            raise ValueError(f'{pack} is not of class file_explorer.Package')
        self._pack = pack

    def _set_temp_dir(self):
        self._temp_dir = pathlib.Path(self._file_handler('local', 'temp'), 'create_standard_format', self._pack.key)
        if not self._temp_dir.exists():
            os.makedirs(self._temp_dir)

    def _copy_files_to_temp_dir(self):
        source_files = []
        cnv_path = self._pack.get_file_path(suffix='.cnv', prefix=None)
        source_files.append([cnv_path, cnv_path.name])
        source_files.append([self._pack.get_file_path(suffix='.sensorinfo'), 'sensorinfo.txt'])
        source_files.append([self._pack.get_file_path(suffix='.metadata'), 'metadata.txt'])
        source_files.append([self._pack.get_file_path(suffix='.deliverynote'), 'delivery_note.txt'])

        for item in source_files:
            source_path, name = item
            target_path = pathlib.Path(self._temp_dir, name)
            if target_path.exists() and not self._kwargs.get('overwrite'):
                raise FileExistsError(target_path)
            shutil.copy2(source_path, target_path)

    def _create_standard_format(self):
        all_file_paths = [path for path in self._temp_dir.iterdir()]
        stem = [path for path in all_file_paths if path.suffix == '.cnv'][0].stem
        logger.debug(f'{all_file_paths=}')
        s = ctdpy_session.Session(filepaths=[str(path) for path in all_file_paths],
                                  reader='smhi')
        datasets = s.read()

        data_path = s.save_data(datasets,
                                writer='ctd_standard_template',
                                keep_original_file_names=True,
                                return_data_path=True)

        # Creation is threaded
        import time
        time.sleep(.1)

        source_dir = pathlib.Path(data_path)
        source_path = pathlib.Path(source_dir, f'{stem}.txt')
        target_dir = self._file_handler('local', 'data')
        target_path = pathlib.Path(target_dir, f'{self._pack.key}.txt')
        if target_path.exists() and not self._kwargs.get('overwrite'):
            return
            raise FileExistsError(target_path)
        shutil.copy2(source_path, target_path)

    def create_from_package(self, pack):
        self._set_pack(pack)
        self._set_temp_dir()
        self._copy_files_to_temp_dir()
        self._create_standard_format()
        self._add_svepa_info(pack)

    def _add_svepa_info(self, pack):
        try:
            import svepa
        except:
            logger.warning(f'Could not import module svepa to add svepa information')
            return
        info = svepa.get_svepa_info(platform=pack.platform, time=pack.datetime)
        # if not info:
        #     logger.info(f'No svepa information for file: {pack.key}')
        #     return
        # logger.debug(f'Svepa {info=}')
        # file_explorer.seabird.add_event_id(pack, **info, overwrite=True)


class temp_CreateStandardFormat:

    def __init__(self, paths_object):
        self.paths = paths_object
        self._packs = []
        self._overwrite = False
        self._metadata_path = None
        self._export_directory = None
        self._output_dir = None

        self._sensorinfo_file_path = None
        self._metadata_file_path = None
        self._deliverynote_file_path = None

    def create_from_directory(self, directory, **kwargs):
        packs = file_explorer.get_packages_in_directory(directory, as_list=True)
        self._create_files(packs, **kwargs)

    def create_from_file_list(self, file_list, **kwargs):
        packs = [file_explorer.get_package_for_file(path) for path in file_list]
        self._create_files(packs, **kwargs)

    def create_from_package_list(self, packages, **kwargs):
        self._create_files(packages, **kwargs)

    def _create_files(self, packs, overwrite=False, **kwargs):

        self._output_dir = pathlib.Path(self.paths.get_local_directory('temp'), 'delivery_files',
                                        datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        if not self._output_dir.exists():
            os.makedirs(self._output_dir)

        self._packs = packs
        self._cnv_files = [pack.get_file_path(suffix='.cnv', prefix=None) for pack in self._packs]
        self._overwrite = bool(overwrite)

        self._create_sensorinfo_file()
        self._create_metadata_file(**kwargs)
        self._create_deliverynote_file(**kwargs)
        self._create_standard_format_files()
        self._copy_standard_format_files_to_local()

    def _create_sensorinfo_file(self):
        create_sensor_info_files_from_cnv_files(self._cnv_files,
                                                self.paths.get_path('instrumentinfo_file'),
                                                output_dir=self._output_dir)
        sensorinfo = CreateSensorInfoSummaryFile(self._output_dir)
        self._sensorinfo_file_path = sensorinfo.write_summary_to_file()

    def _create_metadata_file(self, **kwargs):
        metadata = CreateMetadataFile(package=self._packs, **kwargs)
        self._metadata_file_path = metadata.write_to_file(self._output_dir)

    def _create_deliverynote_file(self, **kwargs):
        delivery = CreateDeliveryNote(packages=self._packs,
                                      **kwargs,
                                      )
        self._deliverynote_file_path = delivery.write_to_file(self._output_dir)

    def _create_standard_format_files(self):
        all_file_paths = self._cnv_files + [self._sensorinfo_file_path, self._metadata_file_path,
                                            self._deliverynote_file_path]
        s = ctdpy_session.Session(filepaths=all_file_paths,
                                  reader='smhi')
        datasets = s.read()
        print('#' * 50)
        for f in sorted(all_file_paths):
            print(f)

        data_path = s.save_data(datasets,
                                writer='ctd_standard_template',
                                keep_original_file_names=True,
                                return_data_path=True)

        self._export_directory = pathlib.Path(data_path)

    def _copy_standard_format_files_to_local(self):
        target_dir = self.paths.get_local_directory('data', create=True)
        cnv_file_stems = [path.stem for path in self._cnv_files]

        for source_path in self._export_directory.iterdir():
            if source_path.stem not in cnv_file_stems:
                continue
            target_path = pathlib.Path(target_dir, source_path.name)
            if target_path.exists() and not self._overwrite:
                raise exceptions.FileExists(target_path)
            shutil.copy2(source_path, target_path)


def create_standard_format_files(*all_file_paths, output_dir=None, overwrite=False):
    s = ctdpy_session.Session(filepaths=all_file_paths,
                              reader='smhi')
    datasets = s.read()
    # print('#' * 50)
    # for f in sorted(all_file_paths):
    #     print(f)

    data_path = s.save_data(datasets,
                            writer='ctd_standard_template',
                            keep_original_file_names=True,
                            return_data_path=True)

    source_dir = pathlib.Path(data_path)
    if not output_dir:
        return source_dir

    file_stems = [path.stem for path in all_file_paths]

    for source_path in source_dir.iterdir():
        if source_path.stem not in file_stems:
            continue
        target_path = pathlib.Path(output_dir, source_path.name)
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        shutil.copy2(source_path, target_path)
    return output_dir
