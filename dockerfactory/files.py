import os
from glob import glob

def get_latest_file_change(files):
    latest = 0
    for file in files:
        src = file['src']

        if os.path.isdir(src):
            date = get_latest_file_change(list({'src': x} for x in glob(os.path.join(src, '*'))))
        else:
            date = os.path.getmtime(src)
            if date > latest:
                latest = date

    return int(latest)
