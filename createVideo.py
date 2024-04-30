import logging
from pathlib import Path
from typing import List

import cv2
from cv2 import dnn_superres
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:

    def __init__(self, path: Path, opath: Path, name: str, fps: int, scale_up: bool) -> None:
        """
        Initialize the GenerateVideo class.

        Args:
            path (Path): The input path containing images.
            opath (Path): The output path for saving the video.
            name (str): The name of the output video file.
            fps (int): Frames per second of the output video.
            scale_up (bool): Whether to use upscaling.
        """
        self.path: Path = path
        self.opath: Path = opath
        self.name: str = name
        self.fps: int = fps
        self.scale_up: bool = scale_up

        self._initialize_logging()
        self._initialize_video_writer()
        self._initialize_up_scaling()

    def _initialize_logging(self) -> None:
        """
        Initialize logging configuration.
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def _initialize_video_writer(self) -> None:
        """
        Initialize video writer with the appropriate codec and resolution.
        """
        fourcc = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        resolution = (3840, 2160) if self.scale_up else (1920, 1080)

        self.video_writer = cv2.VideoWriter(str(self.opath / self.name), fourcc, self.fps, resolution)

    def _initialize_up_scaling(self) -> None:
        """
        Initialize the upscaling model if scale_up is True.
        """
        if self.scale_up:
            self.sr = dnn_superres.DnnSuperResImpl.create()
            self.sr.readModel("ESPCN_x2.pb")  # Load the upscaling model
            self.sr.setModel("espcn", 2)  # Set the model and upscaling ratio
            self.scaling_function = self.sr.upsample
        else:
            self.scaling_function = self._no_scaling

    def _no_scaling(self, x):
        """
        Return the input image without scaling.

        Args:
            x: The input image.

        Returns:
            The input image.
        """
        return x

    def make_video(self, path: str) -> None:
        """
        Create a video from images in the specified path.
        """
        image_list: List[str] = get_sorted_image_files(path)

        self.logger.info(f"Creating video {str(self.opath / self.name)} from {len(image_list)} frames")

        # Process each image and write to video
        for img_path in tqdm(image_list, unit="frames", desc="Generation progress"):
            # Read image
            img = cv2.imread(img_path)

            # Optional: Flip the image vertically
            img = cv2.flip(img, 0)

            # Upscale the image if scaling is enabled
            img = self.scaling_function(img)

            # Write the processed image to the video
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
