import subprocess

class SBEBatchFile:
    def __init__(self, file_handler=None, processing_paths=None):
        """
        :param file_paths: SBEProsessingPaths
        """
        self._file_handler = file_handler
        self._processing_paths = processing_paths

    def create_file(self):
        with open(self._processing_paths('file_batch'), 'w') as fid:
            fid.write(f"sbebatch.exe {self._processing_paths('file_setup')} {self._file_handler('local', 'temp')}")

    def run_file(self):
        if not self._processing_paths('file_batch').exists():
            raise FileNotFoundError(f"Batch file not found: {self._processing_paths('file_batch')}")
        subprocess.run(str(self._processing_paths('file_batch')))