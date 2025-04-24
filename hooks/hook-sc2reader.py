# hooks/hook-sc2reader.py
from PyInstaller.utils.hooks import collect_data_files

# collect_data_files récupère tout ce qui n'est pas .py (donc nos .csv)
datas = collect_data_files('sc2reader', include_py_files=False)
