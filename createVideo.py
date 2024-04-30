import logging
from pathlib import Path
from typing import AnyStr

import cv2
from cv2 import dnn_superres
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:

    def __init__(self, path: Path, opath: Path, name: str, fps: int, scale_up: bool) -> None:

        self.__path: Path = path
        self.__opath: Path = opath
        self.__name: str = name
        self.__fps: int = fps
        self.__scale_up: bool = scale_up

        self.__initialize_logging()
        self.__initialize_up_scaling()

    def __initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.__logger = logging.getLogger(__name__)

    def __initialize_up_scaling(self) -> None:
        fourcc = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')

        resolution = (3840, 2160) if self.__scale_up else (1920, 1080)

        self.__video = cv2.VideoWriter(str(self.__opath / self.__name), fourcc, self.__fps, resolution)

        if self.__scale_up:
            self.__sr = dnn_superres.DnnSuperResImpl.create()
            # self.path = "ESPCN_x3.pb"
            # self.sr.readModel(self.path)
            # self.sr.setModel("espcn", 3)
            # result = sr.upsample(img)

            self.__path = "ESPCN_x2.pb"
            self.__sr.readModel(self.__path)
            self.__sr.setModel("espcn", 2)  # set the model by passing the value and the up-sampling ratio

            self.__scaling_function = self.__sr.upsample
        else:
            self.__scaling_function = self.no_scaling

    def no_scaling(self, x):
        return x

    def make_video(self, path: str) -> None:
        image_list: list[AnyStr] = get_sorted_image_files(path)

        self.__logger.info(f"Make mp4 movie {str(self.__opath / self.__name)} from {len(image_list)} frames")

        for img in tqdm(image_list, unit="frames", desc="Generation progress"):
            img_read = cv2.imread(img)
            flipped_img = cv2.flip(img_read, 0)
            upscaled_img = self.__scaling_function(flipped_img)
            self.__video.write(upscaled_img)

    def __del__(self) -> None:
        self.__video.release()
        self.__logger.info(f"MP4 movie {(str(self.__opath / self.__name))} assembled")
