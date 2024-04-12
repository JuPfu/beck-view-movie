import re
from pathlib import Path
from typing import List


def get_sorted_image_files(path: str = "./frames*.png") -> List[str]:
    # Use pathlib.Path to resolve the path
    path: Path = Path(path)

    # Use glob to get a list of matching files
    file_list = path.parent.glob(path.name)

    # Filter only regular files
    file_list = filter(lambda file: file.is_file(), file_list)

    # Define a regular expression pattern for sorting
    pattern = re.compile(r"^(\D*)(\d+)")

    # Sort the file list based on the numeric part of the filenames
    sorted_files = sorted(file_list, key=lambda s: int(pattern.match(s.stem).group(2)))

    # Convert Path objects to strings
    return [str(file) for file in sorted_files]
