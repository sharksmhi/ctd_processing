import yaml
from yaml.loader import SafeLoader
import pathlib


def get_options():
    with open(pathlib.Path(pathlib.Path(__file__).parent, 'options.yaml')) as fid:
        data = yaml.load(fid, Loader=SafeLoader)
    return data
