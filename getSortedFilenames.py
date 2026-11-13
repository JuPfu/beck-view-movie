
import os
import re
from typing import List

from tqdm import tqdm


def get_sorted_image_files(bracketing: bool, path: str = ".") -> List[str]:
    filenames: List[tuple[str, str]] = []

    pattern = (
        re.compile(r"^frame(\d{5})([a-c])$")
        if bracketing
        else re.compile(r"^frame(\d{5})(a)$")
    )

    # Collect directory entries
    directory_files = os.listdir(path)

    # Scan files with progress information
    for filename in tqdm(
        directory_files,
        desc="Collecting image files",
        unit="files",
        mininterval=1
    ):

        # Ignore macOS AppleDouble metadata files
        if filename.startswith("._"):
            continue

        name, extension = os.path.splitext(filename)

        # Only accept PNG files
        if extension.lower() != ".png":
            continue

        match = pattern.match(name)

        if match:
            abs_path = os.path.abspath(os.path.join(path, filename))

            if os.path.isfile(abs_path):
                filenames.append((abs_path, filename))

    # Sort by frame number and exposure label
    sorted_filenames = sorted(
        filenames,
        key=lambda s: (
            pattern.match(os.path.splitext(s[1])[0]).group(1),
            pattern.match(os.path.splitext(s[1])[0]).group(2)
        )
    )

    if bracketing and len(sorted_filenames) % 3 != 0:
        print(
            f"Warning: {len(sorted_filenames) % 3} files "
            "do not fit complete exposure groups."
        )

    print(f"Collected {len(sorted_filenames)} image files.")

    return [x[0] for x in sorted_filenames]
