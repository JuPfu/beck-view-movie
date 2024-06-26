import logging
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
            path (Path): The input path containing images.
            opath (Path): The path to the directory for saving the video.
            name (str): Basename of the output video file.
            fps (int): Frames per second used when assembling the video.
            batch_size (int): Number of images to process per batch.
            num_workers (int): Number of worker threads to use for parallel processing.
            flip_horizontal (bool): Flip frames horizontally
            flip_vertical (bool): Flip frames vertically
        """
        self.path = args.path
        self.opath = args.opath
        self.name = args.name
        self.fps = args.fps
        self.batch_size = min(max(1, args.batch_size), 500)
        self.num_workers = args.num_workers

        self.flip = 2  # no flip

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
        fourcc = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name), fourcc, self.fps, (1920, 1080))

    def process_image(self, img_path: str) -> ndarray:
        """
        Process a single image: read, flip and return the processed image.

        Args:
            img_path (str): Path to the image file.

        Returns:
            The processed image.
        """
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)  # Using cv2.IMREAD_COLOR for faster reading
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

        self.logger.info(f"Creating video from {len(image_list)} 'frames*.png' files in {str(self.opath / self.name)}.")

        # Process images in chunks
        for start in tqdm(range(0, len(image_list), self.batch_size),
                          unit_scale=self.batch_size,
                          desc="Generation progress",
                          unit="frames"):
            end = start + self.batch_size
            batch = image_list[start:end]

            # Process the batch of images and collect the processed images
            processed_images = self.process_batch(batch)

            # Write processed images to the video writer
            for img in processed_images:
                self.video_writer.write(img)

        # Log completion
        self.logger.info(f"Video {str(self.opath / self.name)} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
