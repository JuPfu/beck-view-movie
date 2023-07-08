# importing libraries
import multiprocessing
import os
import time
from typing import AnyStr

import cv2
import reactivex as rx
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:

    def __init__(self) -> None:
        self.__start_time = 0.0

        # Checking the current directory path
        print(f"cwd={os.getcwd()}")

        self.__optimal_thread_count = multiprocessing.cpu_count()
        self.__pool_scheduler = ThreadPoolScheduler(self.__optimal_thread_count)
        # calculate cpu count which will be used to create a ThreadPoolScheduler
        self.__thread_count = multiprocessing.cpu_count()
        self.__thread_pool_scheduler = ThreadPoolScheduler(self.__thread_count)
        print("Cpu count is : {0}".format(self.__thread_count))

        self.__fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        self.__video = cv2.VideoWriter('/Users/jp/PycharmProjects/bv-movie/output_async_video.mp4', self.__fourcc, 18,
                                       #                                                          (1280, 720))
                                       #                             (1920, 1080))
                                       (3840, 2160))
        #                        (3840, 2160))  # (1920, 1080))

        self.__sr = cv2.dnn_superres.DnnSuperResImpl_create()
        # self.path = "ESPCN_x3.pb"
        # self.sr.readModel(self.path)
        # self.sr.setModel("espcn", 3)
        # result = sr.upsample(img)

        self.path = "ESPCN_x2.pb"
        self.__sr.readModel(self.path)
        self.__sr.setModel("espcn", 2)  # set the model by passing the value and the up-sampling ratio

        self.__writeFrameSubject: rx.subject.Subject = rx.subject.Subject()
        self.__writeFrameDisposable = self.__writeFrameSubject.pipe(
            ops.observe_on(self.__thread_pool_scheduler),
            ops.do_action(lambda x: self.__video.write(x)),
            ops.scan(lambda acc, x: acc + 1, 0),
            ops.do_action(lambda x: print(f"wrote image {x}"))
        ).subscribe(
            # on_next=lambda i: print(f"PROCESS writeFrame: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("XXXXXXXXXXXXXX")
        )

        self.__upscaleSubject: rx.subject.Subject = rx.subject.Subject()
        self.__upscaleDisposable = self.__upscaleSubject.pipe(
            ops.map(lambda x: self.__sr.upsample(x)),
            ops.observe_on(self.__thread_pool_scheduler),
            ops.do_action(lambda img: self.__writeFrameSubject.on_next(img)),
        ).subscribe(
            # on_next=lambda i: print(f"PROCESS upscale: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("ZZZZZZZZZ")
        )

        self.__readImgSubject: rx.subject.Subject = rx.subject.Subject()
        self.__readImgObservable = self.__readImgSubject.pipe(
            ops.subscribe_on(self.__thread_pool_scheduler),
            ops.do_action(lambda x: print(f"working on image {x}")),
            ops.map(lambda img: cv2.imread(img)),
            ops.map(lambda img: cv2.flip(img, 1)),
            ops.map(lambda img: cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_CUBIC)),
            ops.do_action(lambda img: self.__upscaleSubject.on_next(img)),
            ops.observe_on(self.__thread_pool_scheduler),
            ops.scan(lambda acc, x: acc + 1, 0),
            ops.do_action(lambda x: print(f"read image {x}"))
        ).subscribe(
            # on_next=lambda i: print(f"PROCESS readIMG: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("finished readIMG")
        )

    def get_images(self, dir_path) -> list[AnyStr]:
        return get_sorted_image_files(dir_path)

    def write_video(self, dir_path: str) -> None:
        self.__start_time = time.time()
        image_list: list[AnyStr] = self.get_images(dir_path)
        for image in image_list:
            img = cv2.imread(image)
            # resized = cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_CUBIC)
            # print(f"===>vor upscale {img.shape}")
            # up_img = self.sr.upsample(resized)
            # up_img = self.upscale_image(resized)
            self.__video.write(img)

        self.__video.release()

    def async_write_video(self, dir_path: str) -> None:
        self.__start_time = time.time()
        image_list: list[AnyStr] = self.get_images(dir_path)

        print(f"async_write_video jetzt gehts los {len(image_list)}")

        rx.from_list(image_list).pipe(
            ops.do_action(lambda x: self.__readImgSubject.on_next(x)),
            ops.observe_on(self.__thread_pool_scheduler),
        ).subscribe(
            # on_next=lambda i: print(
            #    f"VIEW PROCESS async_write_video: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("from list completed")
        )

        time.sleep(2)

    def __del__(self) -> None:
        self.__thread_pool_scheduler.executor.shutdown(wait=True, cancel_futures=False)

        self.__video.release()

        # self.__readImgObservable.dispose()
        # self.__upscaleDisposable.dispose()
        # self.__writeFrameDisposable.dispose()

        print("-------ENDE---------")
        print((time.time() - self.__start_time))
