import file_explorer
import datetime
import pathlib
from ctd_processing import utils


class ASVPfile:

    def __init__(self, pack):
        self.file = pack.get_file(prefix=None, suffix='.cnv')

    def get_header_string(self):
        return f'( SoundVelocity {self.version} {self.id} {self.time} {self.lat} {self.lon} {self.radii} ' \
               f'{self.valid_from} {self.valid_to} {self.src} {self.hist} {self.nr_values} )'

    def write_file(self, file_path=None, overwrite=False):
        if not file_path:
            path = pathlib.Path(self.file.path.parent, f'{self.file.path.stem}.asvp')
            print('a', path)
        else:
            path = pathlib.Path(file_path)
            print('b', path)
        if path.is_file() and path.suffix != '.asvp':
            path = pathlib.Path(path.parent, f'{path.stem}.asvp')
            print('c', path)
        elif path.is_dir():
            path = pathlib.Path(path, f'{self.file.path.stem}.asvp')
            print('d', path)
        if path.exists() and not overwrite:
            raise FileExistsError(path)

        lines = [self.get_header_string()]
        for z, x in zip(self.z_data, self.vel_data):
            lines.append(f'{z:.2f} {x:.2f}')
        lines.append('')
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))

    @property
    def z_data(self):
        try:
            return self.file.get_data(mapped=True)['PRES_CTD']
        except:
            return self.file.data['Pressure, Strain Gauge [db]']

    @property
    def vel_data(self):
        try:
            return self.file.get_data(mapped=True)['SVEL_CTD']
        except:
            return self.file.data['Sound Velocity [Chen-Millero, m/s]']

    @staticmethod
    def format_time(dtime):
        return dtime.strftime('%Y%m%d%H%M')

    @staticmethod
    def format_pos(pos):
        return str(round(utils.decmin_to_decdeg(pos), 6))

    @property
    def version(self):
        return '1.0'

    @property
    def id(self):
        return self.file('serno')

    @property
    def time(self):
        return self.format_time(datetime.datetime.now())

    @property
    def lat(self):
        return self.format_pos(self.file('lat'))

    @property
    def lon(self):
        return self.format_pos(self.file('lon'))

    @property
    def radii(self):
        return '1'

    @property
    def valid_from(self):
        return self.format_time(self.file.datetime)

    @property
    def valid_to(self):
        return self.format_time(self.file.datetime)

    @property
    def src(self):
        return 'CTD'

    @property
    def hist(self):
        return 'P'

    @property
    def nr_values(self):
        return str(len(self.z_data))


if __name__ == '__main__':
    pack = file_explorer.get_packages_in_directory(r'C:\mw\temmp\temp_mh_ibts\local\2022\cnv', as_list=True)[0]
    asvp = ASVPfile(pack)


