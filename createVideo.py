import logging
import os
import pathlib
import sys
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from random import randint
from typing import List

import cv2
from numpy import ndarray
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files
from tqdm_logger import TqdmLogger


class GenerateVideo:

    def __init__(self, args: Namespace) -> None:
        """
        Initialize the GenerateVideo class.
        """

        self._initialize_args(args)
        self._initialize_logging()
        self._initialize_resolution()
        self._initialize_video_writer()

    def _initialize_args(self, args: Namespace) -> None:
        """
        args:
            path (Path): The input path containing images
            opath (Path): The path to the directory for saving the video
            name (str): Basename of the output video file
            fps (int): Frames per second used when assembling the video
            batch_size (int): Number of images to process per batch
            num_workers (int): Number of worker threads to use for parallel processing
            flip_horizontal (bool): Flip frames horizontally
            flip_vertical (bool): Flip frames vertically
            width_height: (str): widthxheight of frames
            codec (str): Codec to be used for video
            gui (bool): Whether beck-view-movie has been started be beck-view-movie-gui and not from the command line
        """

        self.path: pathlib.Path = args.path
        self.opath: pathlib.Path = args.opath
        self.name: str = os.path.splitext(args.name)[0]
        self.output_format: str = args.output_format
        self.fps: float = args.fps
        self.batch_size: int = min(max(1, args.batch_size), 500)
        self.num_workers: int = args.num_workers
        self.width_height: str = args.width_height
        self.width: int = 1920;
        self.height: int = 1080;
        self.codec: str = args.codec

        self.flip: int = 2  # no flip

        if args.flip_horizontal:
            self.flip = 0

        if args.flip_vertical:
            self.flip = 1

        if args.flip_horizontal and args.flip_vertical:  # flip in both directions
            self.flip = -1

        self.gui: bool = args.gui

    def _initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        if self.gui:
            handler = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(handler)

    def _initialize_resolution(self) -> None:

        self.image_list: List[str] = get_sorted_image_files(self.path / "frame*.png")

        if len(self.image_list) == 0:
            self.logger.error(
                f"Found {len(self.image_list)} images in {self.path} - beck-view-movie will be terminated.")
            sys.exit(2)

        if self.width_height != "automatic":
            self.wh: [str] = self.width_height.split("x")
            self.width = int(self.wh[0]) if int(self.wh[0]) >= 48 else 1920
            self.height = int(self.wh[1]) if int(self.wh[1]) >= 48 else 1080
        else:
            index: int = randint(0, len(self.image_list) - 1)
            test_image: ndarray = cv2.imread(self.image_list[index])
            (self.height, self.width, _) = test_image.shape

        self.logger.info(
            f"Creating video from {len(self.image_list)} 'frames*.png' files with resolution {self.width} x {self.height} in {str(self.opath / self.name)}.{self.output_format}.")

    def _initialize_video_writer(self) -> None:
        # self.logger.info(f"Build details: {cv2.getBuildInformation()}")

        resolution = (self.width, self.height)
        # opencv codecs https://gist.github.com/takuma7/44f9ecb028ff00e2132e
        #
        # windows specific notes
        #   output format changes with filename extension
        #   successfully tested postfixes without checking of actual coding in generated files
        #   avi
        #   mp4
        #   m4v
        #   wmv
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name) + "." + self.output_format,
                                            fourcc=fourcc,
                                            fps=self.fps,
                                            frameSize=resolution)

    def process_image(self, img_path: str) -> ndarray:
        """
        Process a single image: read, flip and return the processed image.

        Args:
            img_path (str): Path to the image file.

        Returns:
            The processed image.
        """
        img: ndarray = cv2.imread(img_path, cv2.IMREAD_COLOR)  # Using cv2.IMREAD_COLOR for faster reading
        img = cv2.flip(img, self.flip) if self.flip != 2 else img
        return img

    def process_batch(self, image_paths: List[str]) -> List[ndarray]:
        """
        Process a batch of images in parallel and return the processed images.

        Args:
            image_paths (List[str]): List of image file paths.

        Returns:
            List[ndarray]: List of processed images in the same order as the input list.
        """
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Use map to process images in parallel and maintain order
            processed_images: List[ndarray] = list(executor.map(self.process_image, image_paths))

        return processed_images

    def assemble_video(self) -> None:
        """
        Create a video from images in the specified path using parallel processing in chunks.
        """

        if self.gui:
            progress_bar = tqdm(range(0, len(self.image_list), self.batch_size), unit_scale=self.batch_size,
                                desc="Generation progress", unit="frames", file=TqdmLogger(self.logger), mininterval=5)
        else:
            progress_bar = tqdm(range(0, len(self.image_list), self.batch_size), unit_scale=self.batch_size,
                                desc="Generation progress", unit="frames")

        # Process images in chunks
        for start in progress_bar:
            end: int = start + self.batch_size
            batch: List[str] = self.image_list[start:end]

            # Process the batch of images and collect the processed images
            processed_images: List[ndarray] = self.process_batch(batch)

            # Write processed images to the video writer
            for img in processed_images:
                self.video_writer.write(img)
                del img

        # Log completion
        self.logger.info(f"Video {str(self.opath / self.name)}.{self.output_format} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
