import os
import re
from typing import List


def get_sorted_image_files(bracketing: bool, path: str = ".") -> List[str]:
    filenames: List[tuple[str, str]] = []

    pattern = (
        re.compile(r"^frame(\d{5})([a-c])$")
        if bracketing
        else re.compile(r"^frame(\d{5})(a)$")
    )

    for filename in os.listdir(path):

        # Ignore macOS AppleDouble metadata files
        if filename.startswith("._"):
            continue

        name, extension = os.path.splitext(filename)

        if extension.lower() != ".png":
            continue

        match = pattern.match(name)

        if match:
            abs_path = os.path.abspath(os.path.join(path, filename))

            if os.path.isfile(abs_path):
                filenames.append((abs_path, filename))

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

    return [x[0] for x in sorted_filenames]