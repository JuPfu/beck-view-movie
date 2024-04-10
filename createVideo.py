# importing libraries
import logging
import multiprocessing
import os
import time
from typing import AnyStr

import cv2
import reactivex as rx
from cv2 import dnn_superres
from reactivex import operators as ops, Subject
from reactivex.abc import DisposableBase
from reactivex.scheduler import ThreadPoolScheduler

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:
    logger = None

    processed_frames = 0

    __writeFrameSubject: Subject = None
    __writeFrameDisposable: DisposableBase = None
    __upscaleSubject: Subject = None
    __upscaleDisposable: DisposableBase = None
    __readImgSubject: Subject = None
    __readImgDisposable: DisposableBase = None

    def __init__(self) -> None:
        self.initialize_logging()

        self.__start_time = 0.0

        # Checking the current directory path
        print(f"cwd={os.getcwd()}")

        # calculate cpu count which will be used to create a ThreadPoolScheduler
        self.__thread_count = multiprocessing.cpu_count()
        self.__thread_pool_scheduler = ThreadPoolScheduler(self.__thread_count)
        print("Cpu count is : {0}".format(self.__thread_count))

        fourcc = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        self.__video = cv2.VideoWriter('/Users/jp/PycharmProjects/beck-view-movie/output_async_video.mp4',
                                       fourcc, 24,
        #                               (1280, 720))
         (1920, 1080))
        #                               (3840, 2160))
        #                        (3840, 2160))  # (1920, 1080))

        self.__sr = dnn_superres.DnnSuperResImpl.create()
        # self.path = "ESPCN_x3.pb"
        # self.sr.readModel(self.path)
        # self.sr.setModel("espcn", 3)
        # result = sr.upsample(img)

        self.path = "ESPCN_x2.pb"
        self.__sr.readModel(self.path)
        self.__sr.setModel("espcn", 2)  # set the model by passing the value and the up-sampling ratio

        self.initialize_threads()

    def initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def initialize_threads(self) -> None:
        self.__writeFrameSubject: rx.subject.Subject = rx.subject.Subject()
        self.__writeFrameDisposable = self.__writeFrameSubject.pipe(
            # ops.observe_on(self.__thread_pool_scheduler),
            ops.map(lambda x: self.__video.write(x)),
            ops.scan(lambda acc, x: acc + 1, 0),
            ops.do_action(self.set_processed_frames)
        ).subscribe(
            # on_next=lambda i: print(f"PROCESS writeFrame: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("XXXXXXXXXXXXXX")
        )

        self.__upscaleSubject: rx.subject.Subject = rx.subject.Subject()
        self.__upscaleDisposable = self.__upscaleSubject.pipe(
            # ops.map(lambda x: self.__sr.upsample(x)),
            ops.observe_on(self.__thread_pool_scheduler),
            ops.map(lambda img: self.__writeFrameSubject.on_next(img)),
        ).subscribe(
            # on_next=lambda i: print(f"PROCESS upscale: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: self.__writeFrameSubject.on_completed()
        )

        self.__readImgSubject: rx.subject.Subject = rx.subject.Subject()
        self.__readImgDisposable = self.__readImgSubject.pipe(
            # ops.subscribe_on(self.__thread_pool_scheduler),
            ops.do_action(lambda x: print(f"working on image {x}")),
            ops.map(lambda img: cv2.imread(img)),
            ops.map(lambda img: cv2.flip(img, 0)),
            # ops.map(lambda img: cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_CUBIC)),
            ops.map(lambda img: self.__upscaleSubject.on_next(img)),
            # ops.observe_on(self.__thread_pool_scheduler),
            ops.scan(lambda acc, x: acc + 1, 0),
            # ops.do_action(lambda x: print(f"read image {x}"))
        ).subscribe(
            # on_next=lambda i: print(f"PROCESS readIMG: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: self.__upscaleSubject.on_completed()
        )

    def set_processed_frames(self, count) -> None:
        self.processed_frames = count

    def write_video(self, dir_path: str) -> None:
        self.__start_time = time.time()
        image_list: list[AnyStr] = get_sorted_image_files(dir_path)

        print(f"write_video jetzt gehts los {len(image_list)}")

        rx.from_list(image_list).pipe(
            ops.map(lambda x: self.__readImgSubject.on_next(x)),
            ops.observe_on(self.__thread_pool_scheduler),
        ).subscribe(
            # on_next=lambda i: print(
            #    f"VIEW PROCESS write_video: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=print("finished from list")
        )

        # time.sleep(2)

    def __del__(self) -> None:
        self.__thread_pool_scheduler.executor.shutdown(wait=True, cancel_futures=False)

        self.__video.release()

        elapsed_time = time.time() - self.__start_time
        average_fps = self.processed_frames / elapsed_time if elapsed_time > 0 else 0

        self.logger.info("-------End Of Film---------")
        self.logger.info("Total processed frames: %d", self.processed_frames)
        self.logger.info("Total elapsed time: %.2f seconds", elapsed_time)
        self.logger.info("Average FPS: %.2f", average_fps)

        self.__readImgDisposable.dispose()
        self.__upscaleDisposable.dispose()
        self.__writeFrameDisposable.dispose()
