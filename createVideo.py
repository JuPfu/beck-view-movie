import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List

import cv2
from cv2 import dnn_superres
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:
    def __init__(self, path: Path, opath: Path, name: str, fps: int, scale_up: bool) -> None:
        self.path = path
        self.opath = opath
        self.name = name
        self.fps = fps
        self.scale_up = scale_up

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

    def _no_scaling(self, x):
        return x

    def process_image(self, img_path: str):
        img = cv2.imread(img_path)
        img = cv2.flip(img, 0)
        img = self.scaling_function(img)
        return img

    def make_video(self, path: str) -> None:
        image_list: List[str] = get_sorted_image_files(path)

        self.logger.info(f"Creating video {str(self.opath / self.name)} from {len(image_list)} frames")

        # Use a thread pool executor for parallel processing
        with ThreadPoolExecutor() as executor:
            # Submit image processing tasks and collect them in a list
            futures = [executor.submit(self.process_image, img_path) for img_path in image_list]

            # Create a list to store processed images in order
            processed_images = [future.result() for future in
                                tqdm(futures, total=len(image_list), unit="frames", desc="Generation progress")]

            # Write processed images to video writer in original order
            for img in processed_images:
                self.video_writer.write(img)

        self.logger.info(f"Video {str(self.opath / self.name)} assembled successfully.")

    def __del__(self):
        if hasattr(self, "video_writer"):
            self.video_writer.release()
