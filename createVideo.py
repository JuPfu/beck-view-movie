import logging
import multiprocessing
import time
from pathlib import Path
from typing import AnyStr

import cv2
import reactivex as rx
from cv2 import dnn_superres
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:

    def __init__(self, path: Path, opath: Path, name: str, fps: int, scale_up: bool) -> None:

        self.__path: Path = path
        self.__opath: Path = opath
        self.__name: str = name
        self.__fps: int = fps
        self.__scale_up: bool = scale_up

        self.__processed_frames_count = 0

        self.__initialize_logging()

        print(f"__init__ {opath=}")
        # calculate cpu count which will be used to create a ThreadPoolScheduler
        self.__thread_count = multiprocessing.cpu_count()
        self.__thread_pool_scheduler = ThreadPoolScheduler(self.__thread_count)
        self.__logger.info("Cpu count is : {0}".format(self.__thread_count))

        self.__initialize_up_scaling()

        self.__initialize_threads()

        self.__start_time = 0.0

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

    def __initialize_threads(self) -> None:
        self.__writeFrameSubject: rx.subject.Subject = rx.subject.Subject()
        self.__writeFrameDisposable = self.__writeFrameSubject.pipe(
            ops.map(lambda x: self.__video.write(x)),
            ops.scan(lambda acc, x: acc + 1, 0),
            ops.do_action(self.set_processed_frames_count)
        ).subscribe(
            on_error=lambda e: self.__logger.error(e),
            on_completed=lambda: print("write frame finished")
        )

        self.__upscaleSubject: rx.subject.Subject = rx.subject.Subject()
        self.__upscaleDisposable = self.__upscaleSubject.pipe(
            ops.map(lambda x: self.__scaling_function(x)),
            ops.observe_on(self.__thread_pool_scheduler),
            ops.map(lambda img: self.__writeFrameSubject.on_next(img)),
        ).subscribe(
            on_error=lambda e: self.__logger.error(e),
            on_completed=lambda: self.__writeFrameSubject.on_completed()
        )

        self.__readImgSubject: rx.subject.Subject = rx.subject.Subject()
        self.__readImgDisposable = self.__readImgSubject.pipe(
            ops.map(lambda filename: cv2.imread(filename)),
            ops.map(lambda img: cv2.flip(img, 0)),
            # ops.map(lambda img: cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_CUBIC)),
            ops.map(lambda img: self.__upscaleSubject.on_next(img)),
            ops.observe_on(self.__thread_pool_scheduler),
            ops.scan(lambda acc, x: acc + 1, 0),
        ).subscribe(
            on_error=lambda e: self.__logger.error(e),
            on_completed=lambda: self.__upscaleSubject.on_completed()
        )

    def no_scaling(self, x: cv2.typing.MatLike) -> cv2.typing.MatLike:
        return x

    def set_processed_frames_count(self, count) -> None:
        self.__processed_frames_count = count
        if count % 25 == 0:
            print(f"\n{count}", end="")
        else:
            print(".", end="")

    def make_video(self, path: str) -> None:
        self.__start_time = time.time()
        image_list: list[AnyStr] = get_sorted_image_files(path)

        self.__logger.info(f"Make mp4 movie from {len(image_list)} frames")

        rx.from_list(image_list).pipe(
            ops.map(lambda x: self.__readImgSubject.on_next(x)),
            ops.observe_on(self.__thread_pool_scheduler),
        ).subscribe(
            on_error=lambda e: self.__logger.error(e)
        )

    def __del__(self) -> None:
        self.__thread_pool_scheduler.executor.shutdown(wait=True, cancel_futures=False)

        self.__video.release()

        elapsed_time = time.time() - self.__start_time
        average_fps = self.__processed_frames_count / elapsed_time if elapsed_time > 0 else 0

        self.__logger.info("-------MP4 film assembled---------")
        self.__logger.info("Total processed frames: %d", self.__processed_frames_count)
        self.__logger.info("Total elapsed time: %.2f seconds", elapsed_time)
        self.__logger.info("Average FPS: %.2f", average_fps)

        self.__readImgDisposable.dispose()
        self.__upscaleDisposable.dispose()
        self.__writeFrameDisposable.dispose()
