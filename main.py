import signal
from argparse import Namespace
from multiprocessing import freeze_support
from types import FrameType

from CommandLineParser import CommandLineParser
from createVideo import GenerateVideo


def main():
    freeze_support()

    signal.signal(signal.SIGINT, sigint_handler)

    args: Namespace = CommandLineParser().parse_args()

    generate_video: GenerateVideo = GenerateVideo(args)

    generate_video.assemble_video(str(args.path / "frame*.png"))


def sigint_handler(signum: int, frame: FrameType | None) -> None:
    signame: str = signal.Signals(signum).name
    print(f"\nProgram terminated by signal '{signame}' at {frame}")
    exit(1)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
