from pathlib import Path

import subprocess
import webbrowser


class CTDBokehQC:

    def __init__(self):
        self._run_bokeh_server_template_file = Path(Path(__file__).parent, 'template', 'run_bokeh_server_template.py')
        self._run_bokeh_server_file = Path(Path(__file__).parent, 'run_bokeh_server.py')
        self._run_bokeh_server_bat_file = Path(Path(__file__).parent, 'run_bokeh_server.bat')

        self._bokeh_server = None

    def set_data_directory(self, data_directory):
        lines = []
        with open(self._run_bokeh_server_template_file) as fid:
            for line in fid:
                if line.startswith('DATA_DIR'):
                    lines.append(f"DATA_DIR = r'{data_directory}'\n")
                else:
                    lines.append(line)
        with open(self._run_bokeh_server_file, 'w') as fid:
            fid.writelines(lines)

    def start_bokeh_server(self):
        if self._bokeh_server:
            return
        self._bokeh_server = subprocess.Popen(['bokeh', 'serve', str(self._run_bokeh_server_file)], shell=False, stdout=subprocess.PIPE)
        # self._bokeh_server = subprocess.Popen(str(self._run_bokeh_server_bat_file), shell=False, stdout=subprocess.PIPE)
        webbrowser.open("http://localhost:5006/run_bokeh_server")

    def stop_bokeh_server(self):
        if not self._bokeh_server:
            return
        self._bokeh_server.terminate()
        # self._bokeh_server.kill()
        self._bokeh_server = None


if __name__ == '__main__':
    b = CTDBokehQC()
    b.set_data_directory(r'C:\mw\temp_ctd_pre_system_data_root_server\2021\data')
    b.start_bokeh_server()
