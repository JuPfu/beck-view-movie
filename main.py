from CommandLineParser import CommandLineParser
from createVideo import GenerateVideo

def main():
    args = CommandLineParser().parse_args()

    generate_video = GenerateVideo(args.path, args.opath, args.name, args.fps, args.scaling)

    generate_video.make_video(str(args.path / "frame*.png"))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
