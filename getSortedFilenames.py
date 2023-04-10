import glob
import os
import re
from typing import AnyStr


# pattern = r"^(?:\D*d+\.\D{3,4}"
# prog = re.compile(pattern, flags=0)


def get_filename(file_path) -> AnyStr:
    file_name = os.path.basename(file_path)
    # split into name and extension
    split_tuppel = os.path.splitext(file_name)
    # return name
    return split_tuppel[0]


# search all files of specific type inside a specific folder
def get_image_files(dir_path) -> list[AnyStr]:
    return glob.glob(dir_path)


def get_sorted_image_files(dir_path) -> list[AnyStr]:
    file_list: list[AnyStr] = get_image_files(dir_path)
    filtered_file_list = list(filter(lambda file: os.path.isfile(file), file_list))

    prog = re.compile(r"^(\D*)(\d+)", flags=0)

    filtered_file_list.sort(key=lambda s: int(prog.match(get_filename(s)).group(2)))
    return filtered_file_list
