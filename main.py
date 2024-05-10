from argparse import Namespace
from multiprocessing import freeze_support

from CommandLineParser import CommandLineParser
from createVideo import GenerateVideo


def main():
    freeze_support()

    args: Namespace = CommandLineParser().parse_args()

    generate_video = GenerateVideo(args.path, args.opath, args.name, args.fps)

    generate_video.assemble_video(str(args.path / "frame*.png"))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
