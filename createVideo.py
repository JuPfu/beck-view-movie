import logging
import os
import sys
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from typing import List

import cv2
from cv2 import dnn_superres
from numpy import ndarray
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files
from iagcwd import prepare_image
from tqdm_logger import TqdmLogger


class GenerateVideo:
    def __init__(self, args: Namespace) -> None:
        """
        Initialize the GenerateVideo class.
        """

        self._initialize_args(args)
        self._initialize_logging()
        self._initialize_up_scaling()
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
            scale_up (bool): To up-scale or not to up-scale
            codec (str): Codec to be used for video
        """

        self.path = args.path
        self.opath = args.opath
        self.name = os.path.splitext(args.name)[0]
        self.output_format = args.output_format
        self.fps: float = args.fps
        self.batch_size: int = min(max(1, args.batch_size), 500)
        self.num_workers: int = args.num_workers
        self.wh = args.width_height.split("x")
        self.width: int = int(self.wh[0])
        self.height: int = int(self.wh[1])
        if self.width < 100 or self.height < 100:
            self.width = 1920
            self.height = 1080

        self.scale_up = args.scale_up
        self.codec = args.codec

        self.flip: int = 2  # no flip

        if args.flip_horizontal:
            self.flip = 0

        if args.flip_vertical:
            self.flip = 1

        if args.flip_horizontal and args.flip_vertical:  # flip in both directions
            self.flip = -1

        self.gui = args.gui

    def _initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(handler)

    def _initialize_video_writer(self) -> None:
        # self.logger.info(f"Build details: {cv2.getBuildInformation()}")

        resolution = (3840, 2160) if self.scale_up else (self.width, self.height)
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

    def _initialize_up_scaling(self) -> None:
        if self.scale_up:
            self.sr = dnn_superres.DnnSuperResImpl.create()
            self.sr.readModel("ESPCN_x2.pb")
            self.sr.setModel("espcn", 2)
            self.upscaling_function = self.sr.upsample
        else:
            self.upscaling_function = self._no_scaling

    def _no_scaling(self, img):
        return img

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
        img = self.upscaling_function(img)
        img = prepare_image(img_path, img)
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
            processed_images = list(executor.map(self.process_image, image_paths))

        return processed_images

    def assemble_video(self, path: str) -> None:
        """
        Create a video from images in the specified path using parallel processing in chunks.
        """
        image_list: List[str] = get_sorted_image_files(path)

        self.logger.info(
            f"Creating video from {len(image_list)} 'frames*.png' files in {str(self.opath / self.name) + "." + self.output_format}.")

        if self.gui:
            progress_bar = tqdm(range(0, len(image_list), self.batch_size), unit_scale=self.batch_size,
                                desc="Generation progress", unit="frames", file=TqdmLogger(self.logger), mininterval=5)
        else:
            progress_bar = tqdm(range(0, len(image_list), self.batch_size), unit_scale=self.batch_size,
                                desc="Generation progress", unit="frames")

        # Process images in chunks
        for start in progress_bar:
            end: int = start + self.batch_size
            batch = image_list[start:end]

            # Process the batch of images and collect the processed images
            processed_images = self.process_batch(batch)

            # Write processed images to the video writer
            for img in processed_images:
                self.video_writer.write(img)
                del img

        # Log completion
        self.logger.info(f"Video {str(self.opath / self.name) + "." + self.output_format} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
