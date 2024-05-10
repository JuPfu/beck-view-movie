import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

import cv2
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:
    def __init__(self, path: Path, opath: Path, name: str, fps: int, batch_size: int = 100) -> None:
        """
        Initialize the GenerateVideo class.

        Args:
            path (Path): The input path containing images.
            opath (Path): The path to the directory for saving the video.
            name (str): Basename of the output video file.
            fps (int): Frames per second used when assembling the video.
            batch_size (int): Number of images to process per batch.
        """
        self.path = path
        self.opath = opath
        self.name = name
        self.fps = fps
        self.batch_size = batch_size

        self._initialize_logging()
        self._initialize_video_writer()

    def _initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _initialize_video_writer(self) -> None:
        fourcc = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name), fourcc, self.fps, (1920, 1080))

    def process_image(self, img_path: str):
        """
        Process a single image: read, flip and return the processed image.

        Args:
            img_path (str): Path to the image file.

        Returns:
            The processed image.
        """
        img = cv2.imread(img_path)
        return cv2.flip(img, 0)

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
            [processed_images.append(future.result()) for future in as_completed(futures)]

        return processed_images

    def assemble_video(self, path: str) -> None:
        """
        Create a video from images in the specified path using parallel processing in chunks.
        """
        image_list: List[str] = get_sorted_image_files(path)

        self.logger.info(f"Creating video from {len(image_list)} 'frames*.png' files in  directory {str(path)}.")

        # Process images in chunks
        for start in tqdm(range(0, len(image_list), self.batch_size),
                          unit_scale=self.batch_size,
                          unit_divisor=1000,
                          desc="Generation progress",
                          unit="frames"):
            end = start + self.batch_size
            batch = image_list[start:end]

            # Process the batch of images and collect the processed images
            processed_images = self.process_batch(batch)

            # Write processed images to the video writer
            [self.video_writer.write(img) for img in processed_images]

        # Release video writer and log completion
        self.video_writer.release()
        self.logger.info(f"Video {str(self.opath / self.name)} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
