import glob
import os
import re
from typing import AnyStr


def get_filename(file_path: str) -> AnyStr:
    basename: AnyStr = os.path.basename(file_path)
    # split basename into name and extension
    name, extension = os.path.splitext(basename)
    # return name
    return name


#  supply a list of files matching a pathname pattern
def get_image_files(path: str) -> list[AnyStr]:
    return glob.glob(path)


# get all image files residing in given directory
# sort files in ascending order
def get_sorted_image_files(path: str = "./frames*.png") -> list[AnyStr]:
    file_list: list[AnyStr] = get_image_files(path)
    # keep only files in file list
    filtered_file_list = list(filter(lambda file: os.path.isfile(file), file_list))

    # compile regular expression which is being used as sorting criteria
    pattern: re.Pattern[AnyStr] = re.compile(r"^(\D*)(\d+)", flags=0)

    # in place sorting in ascending order of file list
    filtered_file_list.sort(key=lambda s: int(pattern.match(get_filename(s)).group(2)))
    return filtered_file_list
