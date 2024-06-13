import datetime
import pathlib


class CreateSummaryDeliveryNote:

    def __init__(self):
        self._packs = None
        self._data = None

    def create_from_packages(self, packs, output_dir, **kwargs):
        self._packs = packs
        self._save_info(**kwargs)
        self.write_to_file(output_dir, **kwargs)

    def __str__(self):
        return f'CreateDeliveryNote'

    def _save_info(self, **kwargs):
        year_set = set()
        mprog_set = set()
        proj_set = set()
        orderer_set = set()
        for pack in self._packs:
            mprog_set.add(pack('mprog') or '')
            proj_set.add(pack('proj') or '')
            year_set.add(pack('year') or '')
            orderer_set.add(pack('orderer') or '')

        mprog_set.discard('')
        proj_set.discard('')
        orderer_set.discard('')

        all_orderers = []
        for ord in orderer_set:
            all_orderers.extend([item.strip() for item in ord.split(',')])

        self._data = dict()
        self._data['MYEAR'] = ', '.join(sorted(year_set)) or kwargs.get('MYEAR', '')
        self._data['DTYPE'] = 'PROFILE'
        self._data['MPROG'] = ', '.join(sorted(mprog_set)) or kwargs.get('mprog', '') or kwargs.get('MPROG', '')
        self._data['ORDERER'] = ', '.join(sorted(set(all_orderers))) or kwargs.get('ORDERER', '')
        self._data['PROJ'] = ', '.join(sorted(proj_set)) or kwargs.get('PROJ', '')
        self._data['RLABO'] = kwargs.get('RLABO', '') or 'SMHI'
        self._data['REPBY'] = kwargs.get('contact', '') or kwargs.get('REPBY', '')
        self._data['COMNT_DN'] = kwargs.get('comment', '') or kwargs.get('COMNT_DN', '')
        self._data['DESCR'] = kwargs.get('description', '') or kwargs.get('DESCR', '')
        self._data['FORMAT'] = 'PROFILE'
        self._data['VERSION'] = datetime.datetime.now().strftime('%Y-%m-%d')

        # self._data['data kontrollerad av'] = 'Leverantör'
        # self._data['format'] = 'PROFILE'
        # self._data['projekt'] = ', '.join(sorted(proj_set))
        # self._data['rapporterande institut'] = 'SMHI'
        # self._data['datatype'] = 'PROFILE'
        # self._data['beskrivning av dataset'] = self._description
        # self._data['övervakningsprogram'] = ', '.join(sorted(mprog_set))
        # self._data['beställare'] = ', '.join(sorted(set(all_orderers)))
        # self._data['provtagningsår'] = ', '.join(sorted(year_set))
        # self._data['kontaktperson'] = self._contact
        # self._data['kommentar'] = self._comment

    def write_to_file(self, directory, **kwargs):
        path = pathlib.Path(directory, 'delivery_note.txt')
        if path.exists() and not kwargs.get('overwrite'):
            raise FileExistsError(path)
        lines = []
        for key, value in self._data.items():
            lines.append(f'{key}: {value}')
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path


class CreateDeliveryNote:

    def __init__(self, package, **kwargs):
        self._pack = package
        self._stem = None
        self._save_path = None
        self._data = None
        self._kwargs = kwargs

        self._save_info()

    def __str__(self):
        return f'CreateDeliveryNote'

    def _save_info(self):
        self._data = dict()
        self._data['MYEAR'] = self._pack('year') or self._kwargs.get('MYEAR', '')
        self._data['DTYPE'] = 'PROFILE'
        self._data['MPROG'] = self._pack('mprog') or self._kwargs.get('MPROG', '')
        self._data['ORDERER'] = self._pack('orderer') or self._kwargs.get('ORDERER', '')
        self._data['PROJ'] = self._pack('proj') or self._kwargs.get('PROJ', '')
        self._data['RLABO'] = self._kwargs.get('RLABO', '') or 'SMHI'
        self._data['REPBY'] = self._kwargs.get('contact', '') or self._kwargs.get('REPBY', '')
        self._data['COMNT_DN'] = self._kwargs.get('comment', '') or self._kwargs.get('COMNT_DN', '')
        self._data['DESCR'] = self._kwargs.get('description', '') or self._kwargs.get('DESCR', '')
        self._data['FORMAT'] = 'PROFILE'
        self._data['VERSION'] = datetime.datetime.now().strftime('%Y-%m-%d')

        # self._data['data kontrollerad av'] = 'Leverantör'
        # self._data['format'] = 'PROFILE'
        # self._data['projekt'] = ', '.join(sorted(proj_set))
        # self._data['rapporterande institut'] = 'SMHI'
        # self._data['datatype'] = 'PROFILE'
        # self._data['beskrivning av dataset'] = self._description
        # self._data['övervakningsprogram'] = ', '.join(sorted(mprog_set))
        # self._data['beställare'] = ', '.join(sorted(set(all_orderers)))
        # self._data['provtagningsår'] = ', '.join(sorted(year_set))
        # self._data['kontaktperson'] = self._contact
        # self._data['kommentar'] = self._comment

    def write_to_file(self):
        cnv = self._pack.get_file_path(prefix=None, suffix='.cnv')
        path = pathlib.Path(cnv.parent, f'{cnv.stem}.deliverynote')
        if path.exists() and not self._kwargs.get('overwrite'):
            return
            raise FileExistsError(path)
        lines = []
        for key, value in self._data.items():
            lines.append(f'{key}: {value}')
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))
        return path


def create_deliverynote_summary_file_from_packages(packs, output_dir=None, **kwargs):
    summary = CreateSummaryDeliveryNote()
    return summary.create_from_packages(packs, output_dir=output_dir, **kwargs)
