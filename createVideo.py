import logging
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
from cv2 import dnn_superres
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:
    def __init__(self, path: Path, opath: Path, name: str, fps: int, scale_up: bool, batch_size: int = 100) -> None:
        """
        Initialize the GenerateVideo class.

        Args:
            path (Path): The input path containing images.
            opath (Path): The output path for saving the video.
            name (str): The name of the output video file.
            fps (int): Frames per second of the output video.
            scale_up (bool): Whether to use upscaling.
            batch_size (int): Number of images to process per batch.
        """
        self.path = path
        self.opath = opath
        self.name = name
        self.fps = fps
        self.scale_up = scale_up
        self.batch_size = batch_size

        self._initialize_logging()
        self._initialize_video_writer()
        self._initialize_up_scaling()

    def _initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _initialize_video_writer(self) -> None:
        fourcc = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        resolution = (3840, 2160) if self.scale_up else (1920, 1080)
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name), fourcc, self.fps, resolution)

    def _initialize_up_scaling(self) -> None:
        if self.scale_up:
            self.sr = dnn_superres.DnnSuperResImpl.create()
            self.sr.readModel("ESPCN_x2.pb")
            self.sr.setModel("espcn", 2)
            self.scaling_function = self.sr.upsample
        else:
            self.scaling_function = self._no_scaling

    def _no_scaling(self, img):
        return img

    def process_image(self, img_path: str):
        """
        Process a single image: read, flip, upscale, and return the processed image.

        Args:
            img_path (str): Path to the image file.

        Returns:
            The processed image.
        """
        img = cv2.imread(img_path)
        img = cv2.flip(img, 0)
        img = self.scaling_function(img)
        return img

    def process_batch(self, image_paths: List[str]):
        """
        Process a batch of images in parallel and return the processed images.

        Args:
            image_paths (List[str]): List of image file paths.

        Returns:
            List[cv2.Mat]: List of processed images in the same order as the input list.
        """
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor() as executor:
            # Submit tasks for each image in the batch
            futures = [executor.submit(self.process_image, img_path) for img_path in image_paths]

            # Collect the results in the same order as the input list
            processed_images = []
            for future in as_completed(futures):
                processed_images.append(future.result())

        return processed_images

    def make_video(self, path:  str) -> None:
        """
        Create a video from images in the specified path using parallel processing in chunks.
        """
        image_list: List[str] = get_sorted_image_files(path)

        self.logger.info(f"Creating video {str(self.opath / self.name)} from {len(image_list)} frames")

        # Process images in chunks
        for start in tqdm(range(0, len(image_list), self.batch_size), unit_divisor=1000, desc="Generation progress", unit="frames"):
            end = start + self.batch_size
            batch = image_list[start:end]

            # Process the batch of images and collect the processed images
            processed_images = self.process_batch(batch)

            # Write processed images to the video writer
            for img in processed_images:
                self.video_writer.write(img)

        # Release video writer and log completion
        self.video_writer.release()
        self.logger.info(f"Video {str(self.opath / self.name)} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
        self.logger.info(f"Released video writer for {str(self.opath / self.name)}.")
