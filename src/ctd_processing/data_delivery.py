import shutil
from pathlib import Path

from ctd_processing import delivery_note
from ctd_processing import metadata
from ctd_processing import sensor_info


def create_dv_data_delivery_for_packages(packs, output_dir, **kwargs):
    sorted_packs = sorted(packs)
    sub_dir = Path(output_dir, f'dv_delivery_{sorted_packs[0].date}_{sorted_packs[-1].date}')
    sub_dir.mkdir(parents=True, exist_ok=True)
    sensor_info.create_sensor_info_summary_file_from_packages(packs, output_dir=sub_dir, **kwargs)
    metadata.create_metadata_summary_file_from_packages(packs, output_dir=sub_dir, **kwargs)
    delivery_note.create_deliverynote_summary_file_from_packages(packs, output_dir=sub_dir, **kwargs)

    # Data
    data_dir = Path(sub_dir, 'data')
    data_dir.mkdir(parents=True, exist_ok=True)
    cnv_dir = Path(sub_dir, 'cnv')
    cnv_dir.mkdir(parents=True, exist_ok=True)
    raw_data_dir = Path(sub_dir, 'raw')
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    for pack in packs:
        for source_path in pack.get_file_paths():
            if source_path.suffix in ['.metadata', '.deliverynote', '.jpg']:
                continue
            if source_path.suffix == '.txt':
                target_path = Path(data_dir, source_path.name)
            elif source_path.suffix in ['.cnv', '.sensorinfo']:
                target_path = Path(cnv_dir, source_path.name)
            else:
                target_path = Path(raw_data_dir, source_path.name)

            if target_path.exists() and not kwargs.get('overwrite'):
                raise FileExistsError(target_path)
            shutil.copy2(source_path, target_path)








