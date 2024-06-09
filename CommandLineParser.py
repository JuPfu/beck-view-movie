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
        # Add arguments for input path, output path, movie name and frames per second
        self.parser.add_argument(
            '-p', '--path',
            dest="path",
            type=pathlib.Path,
            nargs='?',
            default=pathlib.Path(".").resolve(),
            help='Path to directory containing png frames - default is current directory.'
        )
        self.parser.add_argument(
            '-o', '--output-path',
            dest="opath",
            type=pathlib.Path,
            nargs='?',
            default=pathlib.Path(".").resolve(),
            help='Output directory for generated mp4 movie - default is current directory'
        )
        self.parser.add_argument(
            '-n', '--name',
            dest="name",
            nargs='?',
            default="beck-view-movie.mp4",
            help='Name of mp4 movie - default is "beck-view-movie.mp4"'
        )
        self.parser.add_argument(
            '-fps', '--frames-per-second',
            dest="fps",
            type=int,
            nargs='?',
            choices=range(15, 31),
            default=24,
            help='Frames per second, usually 18, 21, or 24 - default is 24 fps'
        )
        # Add arguments for horizontal flip
        self.parser.add_argument(
            '-fh', '--flip_horizontal',
            dest="flip_horizontal",
            action="store_true",
            default=False,
            help='Flip frame horizontally'
        )
        # Add arguments for vertical flip
        self.parser.add_argument(
            '-fv', '--flip_vertical',
            dest="flip_vertical",
            action="store_true",
            default=False,
            help='Flip frame vertically'
        )
        self.parser.add_argument(
            '-w',  '--number-of-workers',
            dest="num_workers",
            type=int,
            nargs='?',
            default=8,
            help='Number of parallel worker threads - default is 8 - affects speed of assembly'
        )
        self.parser.add_argument(
            '-bs', '--batch-size',
            dest="batch_size",
            type=int,
            nargs='?',
            default=100,
            help='Batch size for each worker thread - default is 100 - affects speed of assembly'
        )

    def parse_args(self) -> argparse.Namespace:
        # Parse arguments and return the namespace
        return self.parser.parse_args()
