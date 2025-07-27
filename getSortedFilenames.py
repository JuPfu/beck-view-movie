import os
import re
from typing import List


def get_sorted_image_files(bracketing: bool, path: str = ".") -> List[str]:
    filenames: List[tuple[str, str]] = []

    pattern = re.compile(r"^(\D*)(\d{5})([a-c])$") if bracketing else re.compile(r"^(\D*)(\d{5})(a)$")

    for filename in os.listdir(path):
        match = pattern.match(os.path.splitext(filename)[0])
        if match:
            abs_path = os.path.abspath(os.path.join(path, filename))
            if os.path.isfile(abs_path):
                filenames.append((abs_path, filename))

    # Sort first by frame number, then by exposure label (a, b, c)
    sorted_filenames = sorted(
        filenames,
        key=lambda s: (pattern.match(os.path.splitext(s[1])[0]).group(2),
                       pattern.match(os.path.splitext(s[1])[0]).group(3))
    )

    if bracketing and len(sorted_filenames) % 3 != 0:
        print(f"Warning: {len(sorted_filenames) % 3} files do not fit complete exposure groups.")

    return [x[0] for x in sorted_filenames]
