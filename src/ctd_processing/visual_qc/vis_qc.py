from pathlib import Path
import json
import subprocess
import webbrowser
import ctdvis


class VisQC:
    def __init__(self,
                 data_directory=None,
                 visualize_setting='smhi_expedition_vis',
                 filters=None):
        self.data_directory = data_directory
        self.visualize_setting = visualize_setting
        self.filters = filters

        self.settings_argument_file_path = Path(Path(__file__).parent, 'session_ctd_qc_arguments.json')
        self.bokeh_app_file_path = Path(Path(__file__).parent, 'app_to_serve_ctdqc.py')

        self.bokeh_child_process = None

        self._create_settings_argument_file()

    def _create_settings_argument_file(self):
        kwargs = {
            'data_directory': str(self.data_directory),
            'visualize_setting': self.visualize_setting,
            'filters': self.filters,
            'export_folder': str(self.data_directory)
        }
        with open(self.settings_argument_file_path, "w") as fid:
            json.dump(kwargs, fid, indent=4)

    def start(self):
        if self.bokeh_child_process:
            return
        self.bokeh_child_process = subprocess.Popen(['bokeh', 'serve', str(self.bokeh_app_file_path)])
        webbrowser.open('http://localhost:5006/app_to_serve_ctdqc')

    def stop(self):
        if not self.bokeh_child_process:
            return
        self.bokeh_child_process.terminate()
        print(self.bokeh_child_process)
        self.bokeh_child_process = None


if __name__ == '__main__':
    vis = VisQC(data_directory=r'C:/mw/temp_ctd_pre_system_data_root/data',
                visualize_setting='smhi_vis')
    vis.start()



