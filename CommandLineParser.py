import argparse
import pathlib


class CommandLineParser:
    def __init__(self) -> None:
        # Initialize the argument parser with description
        self.parser = argparse.ArgumentParser(
            description='Generate an mp4 video from png files matching the pattern frame{number}.png in a directory.'
        )
        # Add argument for version
        self.parser.add_argument('--version', action='version', version='1.0.0')
        # Add arguments for input path, output path, movie name, frames per second, and scaling
        self.parser.add_argument(
            '-p', '--path',
            dest="path",
            type=pathlib.Path,
            nargs='?',
            default=pathlib.Path(".").resolve(),
            help='Path to directory containing png frames'
        )
        self.parser.add_argument(
            '-o', '--output-path',
            dest="opath",
            type=pathlib.Path,
            nargs='?',
            default=pathlib.Path(".").resolve(),
            help='Output directory for generated mp4 movie'
        )
        self.parser.add_argument(
            '-name', '--name',
            dest="name",
            nargs='?',
            default="beck-view-movie.mp4",
            help='Name of mp4 movie'
        )
        self.parser.add_argument(
            '-fps', '--frames-per-second',
            dest="fps",
            type=int,
            nargs='?',
            choices=[18, 21, 24],
            default=24,
            help='Frames per second, usually 18, 21, or 24 - default is 24 fps'
        )
        self.parser.add_argument(
            '-su', '--scale-up',
            dest="scaling",
            action='store_true',
            default=False,
            help='Scale up movie to a resolution of 3840 x 2160 pixels - default is no upscaling'
        )

    def parse_args(self) -> argparse.Namespace:
        # Parse arguments and return the namespace
        return self.parser.parse_args()
