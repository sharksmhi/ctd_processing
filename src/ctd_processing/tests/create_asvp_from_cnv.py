
import tkinter
from tkinter import filedialog
from datetime import datetime
from file_explorer.seabird.cnv_file import CnvFile
from file_explorer import get_package_for_file
from ctd_processing.asvp_file import ASVPfile


"""
Opens a file dialog to choose a cnv file, then creates an asvp file and writes it to location: output_path
"""

output_path = '\\\\scifi01.svea.slu.se\\Temp\\ASVP\\'


root = tkinter.Tk()
root.wm_attributes('-topmost', 1)
root.withdraw() # stänger tk-fönstret som öppnas

current_year = datetime.now().year

cnv_file_name = filedialog.askopenfilename(filetypes=[('cnv files', '*.cnv')], initialdir=('\\\\scifi01.svea.slu.se\\Scifi\\Processed\\CTD\\%s\\cnv' % current_year), parent=root, title='Select a cnv file')

root.destroy() # tar fullständigt bort tkinter-instansen

# pack = get_package_for_file('C:\\Temp\\SBE19_8438_20250525_0658_77SE_14_0541.cnv')
pack = get_package_for_file(cnv_file_name)

asvp = ASVPfile(pack)
asvp.write_file(file_path=(output_path), overwrite=True)

