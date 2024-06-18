import logging
import os
import pathlib
import shutil

import file_explorer

try:
    import svepa
except ImportError:
    pass
from file_explorer import psa
from file_explorer.file_handler.seabird_ctd import get_seabird_file_handler, SBEFileHandler

from ctd_processing import asvp_file
from ctd_processing import delivery_note
from ctd_processing import metadata
from ctd_processing import modify_cnv
from ctd_processing import sensor_info
from ctd_processing import standard_format
from ctd_processing.processing.sbe_batch_file import SBEBatchFile
from ctd_processing.processing.sbe_processing_paths import SBEProcessingPaths
from ctd_processing.processing.sbe_setup_file import SBESetupFile

logger = logging.getLogger(__name__)


class SBEProcessing:

    def __init__(self, file_handler: SBEFileHandler=None, sbe_processing_paths: SBEProcessingPaths=None, **kwargs):
        self._file_handler = file_handler
        self._processing_paths = sbe_processing_paths

        self._file_path = None
        self._confirmed = False
        self._overwrite = False
        self._package = None
        self._old_key = kwargs.get('old_key', False)

    @property
    def platform(self):
        return self._processing_paths.platform

    @platform.setter
    def platform(self, name):
        # Setting the platform. This is used for prioritising setup files in a specific folder in ctd_config\SBE\processing_psa
        if not name:
            return
        if name.lower() not in self._processing_paths.platforms:
            raise Exception(f'Invalid platform name: {name}')
        self._processing_paths.platform = name

    @property
    def year(self):
        if not self._package:
            return None
        return self._package('year')

    def get_platform_options(self):
        return self._processing_paths.platforms

    def get_surfacesoak_options(self):
        options = {}
        for path in self._processing_paths.loopedit_paths:
            name = path.stem.lower()
            obj = psa.LoopeditPSAfile(path)
            depth_str = str(int(float(obj.depth)))
            parts = name.split('_')
            if len(parts) == 1:
                options[f'Normal: {depth_str} m'] = path
            else:
                options[f'{parts[1].capitalize()}: {depth_str} m'] = path
        return options

    def set_platform(self, platform):
        self._processing_paths.platform = platform

    def set_surfacesoak(self, name):
        """ Sets surfacesoak in setup file. Name must match keys in coming from self.get_surfacesoak_options """
        name = name.lower()
        options = self.get_surfacesoak_options()
        for key, path in options.items():
            if name in key.lower():
                self._processing_paths.set_loopedit(path)
                return (key, path)
        else:
            raise Exception('Invalid surfacesoak option')

    def _get_derive_psa_obj(self):
        return psa.DerivePSAfile(self._processing_paths('psa_derive'))

    def set_tau_state(self, state):
        self._get_derive_psa_obj().set_tau_correction(bool(state))

    def select_file(self, file_path):
        """ Kontrollen för att skriva över bör göras mot raw-mappen istället för mot tempmappen. """
        path = pathlib.Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        self._file_path = path
        self._package = file_explorer.get_package_for_file(path, old_key=self._old_key)
        self._file_handler.set_year(self.year)
        self._confirmed = False

    def confirm_file(self, file_path):
        if not self._file_path:
            raise Exception('No file selected')
        path = pathlib.Path(file_path)
        if not path.samefile(self._file_path):
            raise PermissionError('Confirmed file is not the same as the selected!')
        # Copying files and load instrument files object
        new_path = self._copy_all_files_with_same_file_stem_to_working_dir(path)
        self._package = file_explorer.get_package_for_file(new_path, old_key=self._old_key, no_datetime_from_file_name=True)
        self._package = file_explorer.rename_package(self._package, overwrite=True, old_key=self._old_key)
        self._processing_paths.set_raw_file_path(self._package['hex'])
        self._processing_paths.set_config_suffix(self._package('config_file_suffix'))
        self._setup_file = SBESetupFile(file_handler=self._file_handler,
                                        processing_paths=self._processing_paths,
                                        instrument_files=self._package)
        self._batch_file = SBEBatchFile(file_handler=self._file_handler,
                                        processing_paths=self._processing_paths)
        self._confirmed = True
        return self._package['hex']

    def _copy_raw_files_to_local(self):
        target_directory = self._file_handler('local', 'raw')
        for file in self._package.get_raw_files():
            self._copy_file(file, target_directory, overwrite=self._overwrite)

    def _copy_cnv_files_to_local(self):
        """ Copies cnv-up file to local directory """
        target_directory = self._file_handler('local', 'upcast')
        return self._copy_file(self._package.get_file(suffix='.cnv', prefix='u'), target_directory, overwrite=self._overwrite)

    def _copy_zip_file_to_local(self):
        target_directory = self._file_handler('local', 'raw')
        return self._copy_file(self._package.get_file(suffix='.zip'), target_directory,
                               overwrite=self._overwrite)

    def _copy_plot_files_to_local(self):
        target_directory = self._file_handler('local', 'plots')
        for file in self._package.get_plot_files():
            self._copy_file(file, target_directory, overwrite=self._overwrite)

    def _copy_processed_files_to_local(self):
        self._copy_raw_files_to_local()
        # self._copy_cnv_files_to_local()
        self._copy_zip_file_to_local()
        self._copy_plot_files_to_local()

    def _copy_all_files_with_same_file_stem_to_working_dir(self, file_path):
        target_directory = self._file_handler('local', 'temp')
        stem = file_path.stem.lower()
        return_path = None
        for path in file_path.parent.iterdir():
            if path.stem.lower() == stem:
                return_path = self._copy_file(path, target_directory, overwrite=True)
        return return_path

    def _copy_file(self, source_file, target_directory, overwrite=False):
        if isinstance(source_file, file_explorer.file.InstrumentFile):
            source_file_path = source_file.path
            target_file_path = source_file.get_proper_path(target_directory)
        else:  # pathlib.Path
            source_file_path = source_file
            target_file_path = pathlib.Path(target_directory, source_file.name)

        if target_file_path.exists():
            if not overwrite:
                raise FileExistsError(target_file_path)
            else:
                os.remove(target_file_path)
        shutil.copy2(source_file_path, target_file_path)
        return target_file_path

    def get_file_names_in_server_directory(self, subfolder=None):
        directory = self._file_handler.get_server_directory(subfolder)
        return [path.name for path in directory.iterdir()]

    def _check_files_mismatch(self):
        from file_explorer.seabird import compare
        datcnv = self._processing_paths.get_psa_path('datcnv')
        if not datcnv:
            raise FileNotFoundError('Could not find datcnv-file')
        xmlcon = self._package.get_file_path(suffix=self._package('config_file_suffix'))
        mismatch = compare.get_datcnv_and_xmlcon_pars_mismatch(datcnv=datcnv,
                                                               xmlcon=xmlcon)
        if mismatch:
            raise compare.MismatchWarning(data=mismatch)

    def _try_fixing_mismatch(self):
        from file_explorer.psa.datcnv import ManipulateDatCnv
        datcnv = self._processing_paths.get_psa_path('datcnv')
        if not datcnv:
            raise FileNotFoundError('Could not find datcnv-file')
        xmlcon = self._package.get_file_path(suffix=self._package('config_file_suffix'))
        man = ManipulateDatCnv(datcnv)
        man.remove_parameters_not_in_xmlcon(xmlcon)

    def run_process(self, overwrite=False, ignore_mismatch=False, try_fixing_mismatch=False, **kwargs):
        if not self._confirmed:
            raise Exception('No file confirmed!')
        if try_fixing_mismatch:
            self._try_fixing_mismatch()
        elif not ignore_mismatch:
            self._check_files_mismatch()
        self._overwrite = bool(overwrite)
        self._setup_file.create_file()
        self._batch_file.create_file()
        self._batch_file.run_file()

        key = self._package.key

        print('BEFORE')
        print(self._file_handler('local', 'temp'))
        file_explorer.update_package_with_files_in_directory(self._package, self._file_handler('local', 'temp'))
        print('AFTER')

        modify_cnv.modify_cnv_down_file(self._package,
                                        directory=self._file_handler('local', 'cnv'),
                                        overwrite=self._overwrite)

        self.create_zip_with_psa_files()
        self._package = file_explorer.get_package_for_key(key, directory=self._file_handler('local', 'temp'),
                                                          exclude_directory='create_standard_format',
                                                          exclude_string='ctd_std_fmt',
                                                          **kwargs)
        print(f'A {self._package=}')
        self._copy_processed_files_to_local()
        self._package = file_explorer.get_package_for_file(self._package['hex'],
                                                           directory=self._file_handler('local'),
                                                           exclude_directory='temp', **kwargs)
        print(f'B {self._package=}')
        return self._package

    def create_zip_with_psa_files(self):
        from zipfile import ZipFile
        hex_file = self._package.get_file(suffix='.hex')
        path = pathlib.Path(hex_file.path.parent, f'{self._package.key}_psa_config.zip')
        with ZipFile(path, 'w') as zip_obj:
            for psa_path in self._processing_paths.get_psa_paths():
                zip_obj.write(str(psa_path), psa_path.name)


class SBEPostProcessing:
    """
    Class to handle post processing tasks.
    This class is not intended to be used directly.
    It can be tricky to call all methods in the right order.
    """

    def __init__(self, package, file_handler: SBEFileHandler, **kwargs):
        if not isinstance(package, file_explorer.Package):
            raise ValueError(f'{package} is not of class file_explorer.Package')
        self._pack = package
        self._kwargs = kwargs

        if file_handler:
            self._file_handler = file_handler
        # elif target_root_directory:
        #     self._file_handler = get_seabird_file_handler()
        #     self._file_handler.set_root_dir('local', target_root_directory)
        else:
            raise AttributeError

        self._file_handler.set_year(self._pack('year'))

    @property
    def pack(self):
        return self._pack

    # def set_config_root_directory(self, config_root_directory):
    #     self._file_handler.set_root_dir('config', config_root_directory)

    def create_all_files(self):
        self.create_sensorinfo_file()
        self.create_metadata_file()
        self.create_deliverynote_file()
        self.update_package()
        self.create_standard_format_file()
        return self._pack

    def create_sensorinfo_file(self):
        sensor_info.create_sensor_info_files_from_package(self._pack,
                                                          self._file_handler.instrument_file_path,
                                                          **self._kwargs)

    def create_metadata_file(self):
        meta = metadata.CreateMetadataFile(package=self._pack, **self._kwargs)
        meta.write_to_file()

    def create_deliverynote_file(self):
        delivery = delivery_note.CreateDeliveryNote(package=self._pack, **self._kwargs)
        delivery.write_to_file()

    def update_package(self):
        file_explorer.update_package_with_files_in_directory(self._pack, self._pack.get_file_path(prefix=None, suffix='.cnv').parent, **self._kwargs)

    def create_standard_format_file(self):
        obj = standard_format.CreateStandardFormat(file_handler=self._file_handler, **self._kwargs)
        obj.create_from_package(self._pack)
        file_explorer.update_package_with_files_in_directory(self._pack, self._file_handler('local', 'data'),
                                                             **self._kwargs)
        #self._add_svepa_info()
        file_explorer.update_package_with_files_in_directory(self._pack, self._file_handler('local', 'data'),
                                                             replace=True, **self._kwargs)

    def _add_svepa_info(self):
        info = svepa.get_svepa_info(platform=self._pack.platform, time=self._pack.datetime)
        if not info:
            logger.info(f'No svepa information for file: {self._pack.key}')
            return
        file_explorer.seabird.add_event_id(self._pack, **info, overwrite=True)


class SBEProcessingHandler:
    """
    This class is not intended to be used directly.
    It can be tricky to call all methods in the right order.
    Use a function in __init__.py that suits your needs.
    """

    def __init__(self, target_root_directory=None, file_handler=None, **kwargs):
        self.target_root_directory = target_root_directory
        self._kwargs = kwargs
        self._overwrite = kwargs.get('overwrite', False)
        self.config_root_directory = None
        self.file_path = None
        self._pack = None
        self.post = None

        if file_handler:
            self._file_handler = file_handler
        elif target_root_directory:
            self._file_handler = get_seabird_file_handler()
            self._file_handler.set_root_dir('local', target_root_directory)
            self._file_handler.create_dirs('local')
        else:
            raise AttributeError
        self.sbe_processing_paths = SBEProcessingPaths(self._file_handler)
        self.sbe_processing = SBEProcessing(file_handler=self._file_handler,
                                            sbe_processing_paths=self.sbe_processing_paths, **self._kwargs)

    @property
    def pack(self):
        return self._pack

    def set_config_root_directory(self, config_root_directory=None):
        if not config_root_directory:
            return
        self._file_handler.set_root_dir('config', config_root_directory)
        self.config_root_directory = config_root_directory

    def select_and_confirm_file(self, file_path=None, **kwargs):
        self.file_path = pathlib.Path(file_path)
        self._kwargs.update(kwargs)
        self._pack = file_explorer.get_package_for_file(file_path, **self._kwargs)
        self.sbe_processing.select_file(self._pack['hex'])
        self.sbe_processing.confirm_file(self._pack['hex'])

    def load_psa_config_zip(self):
        if not self._pack['zip']:
            raise Exception('No zip file with psa files found')
        self.sbe_processing_paths.load_psa_config_zip(self._pack['zip'])

    def load_psa_config_list(self, psa_paths=None):
        self.sbe_processing_paths.update_psa_paths(psa_paths or [])

    def reload_package(self, exclude_directory=None):
        if not self._pack:
            return
        self._pack = file_explorer.get_package_for_key(self._pack.key,
                                                      directory=self._file_handler('local'),
                                                      exclude_directory=exclude_directory)

    def set_options(self, **kwargs):
        self._kwargs.update(kwargs)
        self.sbe_processing_paths.platform = self._kwargs.get('platform', 'sbe09')
        self.sbe_processing.set_surfacesoak(self._kwargs.get('surfacesoak', 'normal'))
        self.sbe_processing.set_tau_state(self._kwargs.get('tau', False))

    def process_file(self, **kwargs):
        self._kwargs.update(kwargs)
        self._pack = self.sbe_processing.run_process(**self._kwargs)

    def create_asvp_file(self):
        directory = pathlib.Path(self._kwargs.get('asvp_output_dir', self._pack.get_file_path(prefix=None, suffix='.cnv').parent))
        if self._kwargs.get('delete_old_asvp_files'):
            for path in directory.iterdir():
                if path.suffix != '.asvp':
                    continue
                os.remove(str(path))
        logger.info(f'Creating asvp-file for pack: {self.pack.key} at directory {directory}')
        asvp = asvp_file.ASVPfile(self._pack)
        asvp.write_file(directory, overwrite=self._kwargs.get('overwrite'))
