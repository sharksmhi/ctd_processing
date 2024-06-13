import os
import pathlib


class SBEProcessingPaths:
    """
    Class holds paths used in the SBESetupFile class. SBEProcessingPaths are based on structure of the ctd_config repo.
    For the moment the paths are hardcoded according. Consider putting this information in a config file.

    """

    def __init__(self, file_handler=None):
        """ Config root path is the root path och ctd_config repo """
        self._paths = {}

        self._file_handler = file_handler

        self._platform = None
        self._new_file_stem = None
        self._loopedit_paths = []
        self._platform_paths = {}
        self._psa_names = ['datcnv',
                           'filter',
                           'alignctd',
                           'bottlesum',
                           'celltm',
                           'derive',
                           'binavg',
                           'loopedit',
                           'split',
                           '1-seaplot',
                           '2-seaplot',
                           '3-seaplot',
                           '4-seaplot']

    def __call__(self, key, create=False, **kwargs):
        path = self._paths.get(key)
        if not path:
            raise FileNotFoundError(f'No file found matching key: {key}')
        if create and not path.exists():
            os.makedirs(str(path))
        return path

    def __str__(self):
        return_list = []
        for name in sorted(self._paths):
            return_list.append(f'{name.ljust(15)}: {self._paths[name]}')
        return '\n'.join(return_list)

    def __repr__(self):
        return self.__str__()

    def _save_platform_paths(self):
        """
        Platform paths are based on directories under <config path>/SBE/processing_psa.
        Files in the subfolders are specific for the corresponding "platform"
        """
        self._platform_paths = {}
        for path in pathlib.Path(self._file_handler('config', 'root'), 'SBE', 'processing_psa').iterdir():
            if path.is_file():
                continue
            self._platform_paths[path.name.lower()] = path

    def update_paths(self):
        if self._file_handler.root_dir_is_set('local') and self._file_handler('local', 'temp'):
            # print("= self._file_handler('local', 'temp')", self._file_handler('local', 'temp'))
            self._paths['file_setup'] = pathlib.Path(self._file_handler('local', 'temp'), 'ctdmodule.txt')
            self._paths['file_batch'] = pathlib.Path(self._file_handler('local', 'temp'), 'SBE_batch.bat')

        if self._file_handler.root_dir_is_set('config') and self._file_handler('config', 'root'):
            self._save_platform_paths()

        if self._new_file_stem:
            # print('= self._new_file_stem', self._new_file_stem)
            self._build_raw_file_paths_with_new_file_stem()
            self._build_cnv_file_paths_with_new_file_stem()

        if self._platform:
            # print('= self._platform', self._platform)
            self._build_psa_file_paths()
            self._build_loopedit_file_paths()

    @property
    def loopedit_paths(self):
        self.update_paths()
        return self._loopedit_paths

    @property
    def platforms(self):
        self.update_paths()
        exclude = ['archive', 'common']
        return [name for name in self._platform_paths if name not in exclude]

    @property
    def platform(self):
        return self._platform

    @platform.setter
    def platform(self, platform):
        plat = platform.lower()
        if plat not in self.platforms:
            raise Exception(f'Invalid platform for SBE processing_psa: {platform}')
        self._platform = plat
        self.update_paths()

    def set_raw_file_path(self, file_path):
        """
        Sets file path for the raw files.
        """
        self._new_file_stem = file_path.stem
        self.update_paths()

    def _build_raw_file_paths_with_new_file_stem(self):
        """ Builds the raw file paths from working directory and raw file stem """
        self._paths['config'] = pathlib.Path(self._file_handler('local', 'temp'), f'{self._new_file_stem}.XMLCON')  #
        # Handle
        # CON-files
        self._paths['hex'] = pathlib.Path(self._file_handler('local', 'temp'), f'{self._new_file_stem}.hex')
        self._paths['ros'] = pathlib.Path(self._file_handler('local', 'temp'), f'{self._new_file_stem}.ros')

        for name in ['config', 'hex']:
            if not self._paths[name].exists():
                raise FileNotFoundError(self._paths[name])

    def _build_cnv_file_paths_with_new_file_stem(self):
        """ Builds the cnv file paths from working directory and raw file stem """
        self._paths['cnv'] = pathlib.Path(self._file_handler('local', 'temp'), f'{self._new_file_stem}.cnv')
        self._paths['cnv_down'] = pathlib.Path(self._file_handler('local', 'temp'), f'd{self._new_file_stem}.cnv')
        self._paths['cnv_up'] = pathlib.Path(self._file_handler('local', 'temp'), f'u{self._new_file_stem}.cnv')

    def _build_psa_file_paths(self):
        """
        Builds file paths for the psa files.
        If platform is present then these files ar prioritized.
        Always checking directory ctd_config/SBE/processing_psa/Common
        """
        all_paths = self._get_all_psa_paths()
        self.set_psa_paths(all_paths)

    def _build_loopedit_file_paths(self):
        self._loopedit_paths = []
        for path in self._get_all_psa_paths():
            name = path.name.lower()
            if 'loopedit' in name and name not in self._loopedit_paths:
                self._loopedit_paths.append(path)

    def _get_all_psa_paths(self):
        """
        Returns a list of all psa paths.
        If platform is present then these files ar prioritized.
        Always include paths in directory ctd_config/SBE/processing_psa/Common
        """
        all_paths = []
        if self._platform:
            all_paths.extend(self._get_paths_in_directory(self._platform_paths[self._platform]))
        all_paths.extend(self._get_paths_in_directory(self._platform_paths['common']))
        return all_paths

    @staticmethod
    def _get_paths_in_directory(directory):
        return [path for path in directory.iterdir()]

    def set_loopedit(self, path):
        """ Manually setting the loopedit file """
        path = pathlib.Path(path)
        if 'loopedit' not in path.name.lower():
            raise Exception(f'Invalid LoopEdit file: {path}')
        elif not path.exists():
            raise FileNotFoundError(path)
        self._paths['psa_loopedit'] = path

    def set_config_suffix(self, suffix):
        self._paths['config'] = pathlib.Path(self._file_handler('local', 'temp'), f'{self._new_file_stem}{suffix}')

    def get_psa_paths(self):
        return [value for key, value in self._paths.items() if key.startswith('psa_')]

    def get_psa_path(self, key):
        full_key = f'psa_{key}'
        return self._paths.get(full_key)

    def set_psa_paths(self, psa_paths):
        for name in self._psa_names:
            for path in psa_paths:
                if name not in path.name.lower():
                    continue
                self._paths[f'psa_{name}'] = path
                break
            else:
                raise Exception(f'Could not find psa file associated with: {name}')

    def update_psa_paths(self, psa_paths):
        for name in self._psa_names:
            for path in psa_paths:
                if name not in path.name.lower():
                    continue
                self._paths[f'psa_{name}'] = path
                break

    def load_psa_config_zip(self, zip_path):
        target_dir = pathlib.Path(self._file_handler('local', 'temp'), zip_path.stem)
        from zipfile import ZipFile
        with ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        self.set_psa_paths(list(target_dir.iterdir()))
