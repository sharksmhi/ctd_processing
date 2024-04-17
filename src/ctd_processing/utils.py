import pathlib
import subprocess
import threading
import psutil
import pandas as pd


def git_version():
    """
    Return current version of this github-repository
    :return: str
    """
    version_file = pathlib.Path(pathlib.Path(__file__).absolute().parent.parent, '.git', 'FETCH_HEAD')
    if version_file.exists():
        f = open(version_file, 'r')
        version_line = f.readline().split()
        version = version_line[0][:7]  # Is much longer but only the first 7 letters are presented on Github
        repo = version_line[-1]
        return 'github version "{}" of repository {}'.format(version, repo)
    else:
        return ''


def metadata_string_to_dict(string):
    key_value = [item.strip() for item in string.split('#')]
    data = {}
    for key_val in key_value:
        key, value = [item.strip() for item in key_val.split(':')]
        data[key] = value
    return data


def metadata_dict_to_string(data):
    string_list = []
    for key, value in data.items():
        string_list.append(f'{key}: {value}')
    string = ' # '.join(string_list)
    return string


def _get_running_programs():
    program_list = []
    for p in psutil.process_iter():
        program_list.append(p.name())
    return program_list


def _run_subprocess(line):
    subprocess.run(line)


def run_program(program, line):
    if program in _get_running_programs():
        raise ChildProcessError(f'{program} is already running!')
    t = threading.Thread(target=_run_subprocess(line))
    t.daemon = True  # close pipe if GUI process exits
    t.start()


def get_dataframe_from_file(file_path, **kwargs):
    kw = {'sep': '\t',
          'encoding': 'cp1252'}
    kw.update(kwargs)
    df = pd.read_csv(file_path, **kw)
    df = df.fillna('')
    return df


def get_metadata_string_from_event_ids(event_ids):
    string = metadata_dict_to_string(event_ids)
    return f'EventIDs: {string}'


def get_metadata_event_ids_from_string(string):
    return metadata_string_to_dict(string.split(':', 1)[-1].strip())


def decmin_to_decdeg(pos, return_string=False):
    #    print type(pos),pos
    try:
        if type(pos) in [set, list, tuple]:
            output = []
            for p in pos:
                p = float(p)
                if p >= 0:
                    output.append(np.floor(p / 100.) + (p % 100) / 60.)
                else:
                    output.append(np.ceil(p / 100.) - (-p % 100) / 60.)
        else:
            pos = float(pos)
            if pos >= 0:
                output = np.floor(pos / 100.) + (pos % 100) / 60.
            else:
                output = np.ceil(pos / 100.) - (-pos % 100) / 60.

        if return_string:
            if type(output) is list:
                return map(str, output)
            else:
                return str(output)
        else:
            return output
    except:
        return pos
