import codecs

from file_explorer import psa


class SBESetupFile:
    def __init__(self, file_handler=None, processing_paths=None, instrument_files=None):
        """
        :param file_paths: SBEProsessingPaths
        :param instrument_files: instrumant_files.InstrumentFiles
        """
        self._proc_paths = processing_paths
        self._file_handler = file_handler
        self._package = instrument_files

    def _get_lines(self):

        lines = {}
        lines['datcnv'] = f'datcnv /p{self._proc_paths("psa_datcnv")} /i{self._proc_paths("hex")} /c{self._proc_paths("config")} /o%1'
        lines['filter'] = f'filter /p{self._proc_paths("psa_filter")} /i{self._proc_paths("cnv")} /o%1 '
        lines['alignctd'] = f'alignctd /p{self._proc_paths("psa_alignctd")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'
        lines['celltm'] = f'celltm /p{self._proc_paths("psa_celltm")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'
        lines['loopedit'] = f'loopedit /p{self._proc_paths("psa_loopedit")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'
        lines['derive'] = f'derive /p{self._proc_paths("psa_derive")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'
        lines['binavg'] = f'binavg /p{self._proc_paths("psa_binavg")} /i{self._proc_paths("cnv")} /c{self._proc_paths("config")} /o%1'
        lines['bottlesum'] = self._get_bottle_sum_line()
        lines['split'] = f'split /p{self._proc_paths("psa_split")} /i{self._proc_paths("cnv")} /o%1'

        # station = self._package("station").replace(" ", "_").replace("/", "_")
        # lines['plot1'] = f'seaplot /p{self._proc_paths("psa_1-seaplot")} /i{self._proc_paths("cnv_down")} /a_' \
        #                  f'{station} /o{self._file_handler("local", "temp")} /f{self._package.key}'
        # lines['plot2'] = f'seaplot /p{self._proc_paths("psa_2-seaplot")} /i{self._proc_paths("cnv_down")} ' \
        #                  f'/a_TS_diff_{station} /o{self._file_handler("local", "temp")} /f{self._package.key}'
        # lines['plot3'] = f'seaplot /p{self._proc_paths("psa_3-seaplot")} /i{self._proc_paths("cnv_down")} ' \
        #                  f'/a_oxygen_diff_{station} /o{self._file_handler("local", "temp")} /f{self._package.key}'
        # lines['plot4'] = f'seaplot /p{self._proc_paths("psa_4-seaplot")} /i{self._proc_paths("cnv_down")} ' \
        #                  f'/a_fluor_turb_par_{station} /o{self._file_handler("local", "temp")} /f{self._package.key}'

        return list(lines.values())

    def _get_bottle_sum_line(self):
        bottlesum = ''
        if self._package('number_of_bottles') and self._proc_paths("ros"):
            bottlesum = f'bottlesum /p{self._proc_paths("psa_bottlesum")} /i{self._proc_paths("ros")} /c{self._proc_paths("config")} /o%1 '
        else:
            # 'No bottles fired, will not create .btl or .ros file'
            pass
        return bottlesum

    def create_file(self):
        self._add_station_name_to_plots()
        self._write_lines()

    def _write_lines(self):
        file_path = self._proc_paths('file_setup')
        all_lines = self._get_lines()
        with codecs.open(file_path, "w", encoding='cp1252') as fid:
            fid.write('\n'.join(all_lines))

    def _add_station_name_to_plots(self):
        # for key in sorted(self._proc_paths._paths):
        #    print(key)
        for p in range(1, 5):
            obj = psa.PlotPSAfile(self._proc_paths(f"psa_{p}-seaplot"))
            obj.title = self._package('station', pref_suffix='.hdr')
            obj.save()