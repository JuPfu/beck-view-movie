import logging
import os
import pathlib
import sys
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from random import randint
from typing import List

import cv2
import numpy as np
from numpy import ndarray
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files
from tqdm_logger import TqdmLogger


class GenerateVideo:

    def __init__(self, args: Namespace) -> None:
        """
        Initialize the GenerateVideo class.
        """

        self.calibrate_debevec: cv2.CalibrateDebevec
        self.merge_debevec: cv2.MergeDebevec
        self.tone_map = cv2.TonemapDrago

        self._initialize_args(args)
        self._initialize_logging()
        self._initialize_resolution()
        if self.bracketing: self._initialize_bracketing()
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
            bracketing (bool): Bracketing flag
        """

        self.path: pathlib.Path = args.path
        self.opath: pathlib.Path = args.opath
        self.name: str = os.path.splitext(args.name)[0]
        self.output_format: str = args.output_format
        self.fps: float = args.fps
        self.batch_size: int = min(max(1, args.batch_size), 498)
        self.bracketing: bool = args.bracketing
        if self.bracketing:
            self.batch_size = min(max(3, self.batch_size - (self.batch_size % 3)), 498)
            self.tone_mapper: str = getattr(args, "tone_mapper", "drago").lower()

        self.num_workers: int = args.num_workers
        self.width_height = args.width_height
        self.codec: str = args.codec

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
        if self.gui:
            handler = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(handler)

    def _initialize_resolution(self) -> None:

        self.image_list: List[str] = get_sorted_image_files(self.bracketing, str(self.path))

        self.width = 1920
        self.height = 1080
        if self.width_height != "automatic":
            self.wh: List[str] = self.width_height.split("x")
            self.width: int = int(self.wh[0]) if int(self.wh[0]) >= 100 else 1920
            self.height: int = int(self.wh[1]) if int(self.wh[1]) >= 100 else 1080
        else:
            index: int = randint(0, len(self.image_list) - 1)
            print(f" - {self.image_list[index]=}")
            test_image = cv2.imread(self.image_list[index])

            (self.height, self.width, _) = test_image.shape

        actual_frames = len(self.image_list) // 3 if self.bracketing else len(self.image_list)
        self.logger.info(
            f"Creating video from {actual_frames} processed frames with resolution {self.width} x {self.height} in {str(self.opath / self.name) + "." + self.output_format}.")

    def _initialize_bracketing(self) -> None:
        self.times: ndarray[np.float32] = np.asarray([128.0, 256.0, 64.0], dtype=np.float32)
        self.calibrate_debevec = cv2.createCalibrateDebevec()
        self.merge_debevec = cv2.createMergeDebevec()

        if self.tone_mapper == "drago":
            self.logger.info("Using TonemapDrago (bias=2.2)")
            self.tone_map = cv2.createTonemapDrago(2.2)
        elif self.tone_mapper == "reinhard":
            self.logger.info("Using TonemapReinhard (intensity=0.0, light_adapt=1.0, color_adapt=0.0)")
            self.tone_map = cv2.createTonemapReinhard(1.0, 0.0, 1.0, 0.0)
        elif self.tone_mapper == "mantiuk":
            self.logger.info("Using TonemapMantiuk (scale=1.0, saturation=1.0)")
            self.tone_map = cv2.createTonemapMantiuk(1.0, 1.0, 1.0)
        else:
            raise ValueError(f"Unknown tone mapper: {self.tone_mapper}")


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
        fourcc = cv2.VideoWriter.fourcc(*self.codec)
        print(f"{fourcc=}")
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name) + "." + self.output_format,
                                            fourcc=fourcc,
                                            fps=self.fps,
                                            frameSize=resolution)

    def _preload_image_groups(self, grouped_paths: List[List[str]]) -> List[List[ndarray]]:
        """
        Preload image groups (each group is a list of file paths) in parallel and return loaded ndarrays.

        Args:
            grouped_paths (List[List[str]]): Groups of image paths (1 or 3 depending on bracketing).

        Returns:
            List[List[ndarray]]: Loaded image arrays grouped accordingly.
        """

        def load_group(paths: List[str]) -> List[ndarray]:
            images = []
            for path in paths:
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                if img is None:
                    raise ValueError(f"Failed to load image: {path}")
                img = cv2.flip(img, self.flip) if self.flip != 2 else img
                images.append(img)
            return images

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            return list(executor.map(load_group, grouped_paths))


    def process_batch(self, image_paths: List[str]) -> List[ndarray]:
        """
        Process a batch of images in parallel and return the processed images.

        Args:
            image_paths (List[str]): List of image file paths.

        Returns:
            List[ndarray]: List of processed images in the same order as the input list.
        """

        def group(sequence, chunk_size) -> List[List[str]]:
            return [sequence[i:i + chunk_size] for i in range(0, len(sequence), chunk_size)]

        group_size = 3 if self.bracketing else 1
        grouped_paths: List[List[str]] = group(image_paths, group_size)

        # Step 1: Preload all groups
        preloaded_images: List[List[ndarray]] = self._preload_image_groups(grouped_paths)

        # Step 2: Process HDR or single images
        def process(images: List[ndarray]) -> ndarray:
            if not self.bracketing:
                return images[0]  # already flipped
            response = self.calibrate_debevec.process(images, self.times)
            hdr = self.merge_debevec.process(images, self.times, response)
            ldr = self.tone_map.process(hdr)
            return (ldr * 256).astype(dtype=np.uint8)

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            return list(executor.map(process, preloaded_images))

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
            # if bracketing is on batch_size must be a multiple of exposures bracketing - at the moment this should be a multiple of three
            end: int = start + self.batch_size
            batch = self.image_list[start:end]

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
