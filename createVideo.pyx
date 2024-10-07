# distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION

# cython: language_level=3
# cython.infer_types(True)

import cython

import numpy as np              # Import numpy for Python-level use
cimport numpy as np             # Import numpy for uint8 type

import logging
import os
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from typing import List

import cv2
from numpy import ndarray
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:
    def __init__(self, args: Namespace) -> None:
        """
        Initialize the GenerateVideo class.
        """

        self._initialize_args(args)
        self._initialize_logging()
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
            width_height: (int, int): width and height of frames
        """
        self.path = args.path
        self.opath = args.opath
        self.name = os.path.splitext(args.name)[0]
        self.output_format = args.output_format
        self.fps: float = args.fps
        self.batch_size: int = min(max(1, args.batch_size), 500)
        self.num_workers: int = args.num_workers
        self.width, self.height = args.width_height
        if self.width < 100 or self.height < 100:
            self.width = 1920
            self.height = 1080

        self.flip: int = 2  # no flip

        if args.flip_horizontal:
            self.flip = 0

        if args.flip_vertical:
            self.flip = 1

        if args.flip_horizontal and args.flip_vertical:  # flip in both directions
            self.flip = -1

    def _initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _initialize_video_writer(self) -> None:
        self.logger.info(f"Build details: {cv2.getBuildInformation()}")
        # windows specific notes
        #   output format changes with filename extension
        #   successfully tested postfixes without checking of actual coding in generated files
        #   avi
        #   mp4
        #   mp4v
        #   m4v
        #   wmv
        fourcc: int = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name) + "." + self.output_format,
                                            fourcc=fourcc,
                                            fps=self.fps,
                                            frameSize=(self.width, self.height))

    def process_image(self, img_path: str) -> ndarray:
        """
        Process a single image: read, flip and return the processed image.

        Args:
            img_path (str): Path to the image file.

        Returns:
            The processed image.
        """
        img: ndarray = cv2.imread(img_path, cv2.IMREAD_COLOR)  # Using cv2.IMREAD_COLOR for faster reading
        return cv2.flip(img, self.flip) if self.flip != 2 else img

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
            f"Creating video from {len(image_list)} 'frames*.png' files in {str(self.opath / self.name) + '.' + self.output_format}.")

        # Process images in chunks
        for start in tqdm(range(0, len(image_list), self.batch_size),
                          unit_scale=self.batch_size,
                          desc="Generation progress",
                          unit="frames"):
            end: int = start + self.batch_size
            batch = image_list[start:end]

            # Process the batch of images and collect the processed images
            processed_images = self.process_batch(batch)

            # Write processed images to the video writer
            for img in processed_images:
                self.video_writer.write(img)

        # Log completion
        self.logger.info(f"Video {str(self.opath / self.name) + '.' + self.output_format} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
