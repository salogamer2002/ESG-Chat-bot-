import os
from pathlib import Path

def get_all_files(directory, extensions=('.pdf', '.docx')):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                yield os.path.join(root, file)
