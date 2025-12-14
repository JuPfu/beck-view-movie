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
            '-p', '--input-path',
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
            type=pathlib.Path,
            nargs='?',
            default="beck-view-movie",
            help='Name of mp4 movie - default is "beck-view-movie"'
        )
        self.parser.add_argument(
            '-of', '--output-format',
            dest="output_format",
            type=str,
            nargs='?',
            choices=["avi", "mkv", "mov", "mp4", "m4v", "wmv"],
            default="mp4",
            help='Output format of generated video file - allowed values "avi", "mp4", "mp4v", "m4v", "wmv" - default is "mp4"'
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
            '-fh', '--flip-horizontal',
            dest="flip_horizontal",
            action="store_true",
            default=False,
            help='Flip frame horizontally'
        )
        # Add arguments for vertical flip
        self.parser.add_argument(
            '-fv', '--flip-vertical',
            dest="flip_vertical",
            action="store_true",
            default=True,
            help='Flip frame vertically'
        )
        self.parser.add_argument(
            '-w', '--number-of-workers',
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
        self.parser.add_argument(
            '-wh', '--width-height',
            dest="width_height",
            type=str,
            nargs='?',
            default="automatic",
            help='Width and height of image frames - default is "automatic" detection of width and height'
        )
        self.parser.add_argument(
            '-c', '--codec',
            dest="codec",
            type=str,
            choices=["avc1", "h263", "h264", "h265", "mjpg", "mpv4", "xvid", "x264"],
            nargs='?',
            default="avc1",  # which is a H.264 encoder
            help='Supported codecs. See https://gist.github.com/takuma7/44f9ecb028ff00e2132e for more information.'
        )
        # Add arguments for exposure bracketing
        self.parser.add_argument(
            '-b', '--bracketing',
            dest="bracketing",
            action="store_true",
            default=False,
            help='Take multiple exposures of one frame with varying exposure time - default is no bracketing, which means just one exposure per frame'
        )
        self.parser.add_argument(
            '-t', "--tone_mapper",
            type=str,
            choices=["drago", "reinhard", "mantiuk"],
            default="drago",
            help="Tone mapping algorithm to use for HDR processing."
        ),
        self.parser.add_argument(
            "--drago-bias",
            type=float,
            default=2.2
        ),
        self.parser.add_argument(
            "--reinhard-gamma",
            type=float,
            default=1.0
        ),
        self.parser.add_argument(
            "--reinhard-intensity",
            type=float,
            default=0.0
        ),
        self.parser.add_argument(
            "--reinhard-light-adapt",
            type=float,
            default=1.0
        ),
        self.parser.add_argument(
            "--reinhard-color-adapt",
            type=float,
            default=0.0
        ),
        self.parser.add_argument(
            "--mantiuk-scale",
            type=float,
            default=1.0
        ),
        self.parser.add_argument(
            "--mantiuk-saturation",
            type=float,
            default=1.0
        ),
        self.parser.add_argument(
            "--mantiuk-bias",
            type=float,
            default=1.0
        ),
        self.parser.add_argument(
            "--tone-mapper-preset",
            type=str,
            choices=["default", "cinematic", "natural", "highlight", "soft", "vivid", "neutral"],
            default="default"
        ),
        self.parser.add_argument(
            '-g', '--gui',
            dest="gui",
            action="store_true",
            default=False,
            help='beck-view-movie started from beck-view-movie-gui - default is false'
        )

    def parse_args(self) -> argparse.Namespace:
        # Parse arguments and return the namespace
        return self.parser.parse_args()
