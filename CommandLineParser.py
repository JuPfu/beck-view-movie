import argparse
import pathlib


class CommandLineParser:

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description='All png files which match the pattern frame{number}.png in a given directory are used to '
                        'generate a mp4 video.')
        self.parser.add_argument('--version', action='version', version='1.0.0')
        self.parser.add_argument('-p', '--path', type=lambda p: pathlib.Path(p).resolve(), nargs='?',
                                 default=pathlib.Path(".").resolve(), dest="path",
                                 help='path to directory containing png frames')
        self.parser.add_argument('-o', '--output-path', type=lambda p: pathlib.Path(p).resolve(), nargs='?',
                                 default=pathlib.Path(".").resolve(), dest="opath",
                                 help='output directory for generated mp4 movie')
        self.parser.add_argument('-name', '--name', nargs='?',
                                 default="beck-view-movie.mp4",
                                 dest="name",
                                 help='name of mp4 movie')
        self.parser.add_argument('-fps', '--frames-per-second', type=int, nargs='?',
                                 choices=[18, 21, 24], default=24, dest="fps",
                                 help='usually 18, 21 or 24 frames per second - default is 24 fps')
        self.parser.add_argument('-su', '--scale-up', dest='scaling',
                                 action='store_true', default=False,
                                 help='scale up movie to a resolution of 3840 x 2160 pixels - default is no up scaling')

    def parse_args(self) -> argparse.Namespace:
        return self.parser.parse_args()
