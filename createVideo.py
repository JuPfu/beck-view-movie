# importing libraries
import multiprocessing
import os
import time
from threading import current_thread
from typing import AnyStr

import cv2
import reactivex as rx
from reactivex import operators as ops
from reactivex.scheduler import ThreadPoolScheduler

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:

    def __init__(self) -> None:
        self.start_time = 0

        # Checking the current directory path
        print(f"cwd={os.getcwd()}")

        self.optimal_thread_count = multiprocessing.cpu_count()
        self.pool_scheduler = ThreadPoolScheduler(self.optimal_thread_count)
        # calculate cpu count which will be used to create a ThreadPoolScheduler
        self.thread_count = multiprocessing.cpu_count()
        self.thread_pool_scheduler = ThreadPoolScheduler(self.thread_count)
        print("Cpu count is : {0}".format(self.thread_count))

        self.fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        self.video = cv2.VideoWriter('/Users/jp/PycharmProjects/bv-movie/output_async_video.mp4', self.fourcc, 18,
                                     #                             (1280, 720))
                                     #                             (1920, 1080))
                                     (3840, 2160))
        #                        (3840, 2160))  # (1920, 1080))

        self.sr = cv2.dnn_superres.DnnSuperResImpl_create()
        # self.path = "ESPCN_x3.pb"
        # self.sr.readModel(self.path)
        # self.sr.setModel("espcn", 3)
        # result = sr.upsample(img)

        self.path = "ESPCN_x2.pb"
        self.sr.readModel(self.path)
        self.sr.setModel("espcn", 2)  # set the model by passing the value and the upsampling ratio

        self.writeFrameSubject = rx.subject.Subject()
        self.writeFrameDisposable = self.writeFrameSubject.pipe(
            ops.observe_on(self.thread_pool_scheduler),
            ops.map(lambda x: self.video.write(x)),
        ).subscribe(
            on_next=lambda i: print(f"PROCESS writeFrame: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("XXXXXXXXXXXXXX")
        )

        self.upscaleSubject = rx.subject.Subject()
        self.upscaleDisposable = self.upscaleSubject.pipe(
            ops.map(lambda x: self.sr.upsample(x)),
            ops.observe_on(self.thread_pool_scheduler),
            ops.do_action(lambda img: self.writeFrameSubject.on_next(img)),
        ).subscribe(
            on_next=lambda i: print(f"PROCESS upscale: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("ZZZZZZZZZ")
        )

        self.readImgSubject = rx.subject.Subject()
        self.readImgObservable = self.readImgSubject.pipe(
            ops.subscribe_on(self.thread_pool_scheduler),
            ops.map(lambda img: cv2.imread(img)),
            ops.map(lambda img: cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_CUBIC)),
            ops.do_action(lambda img: self.upscaleSubject.on_next(img)),
            ops.observe_on(self.thread_pool_scheduler)
        ).subscribe(
            on_next=lambda i: print(f"PROCESS readIMG: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("finished readIMG")
        )

    def get_images(self, dir_path) -> list[AnyStr]:
        return get_sorted_image_files(dir_path)

    def write_video(self, dir_path) -> None:
        self.start_time = time.time()
        image_list: list[AnyStr] = self.get_images(dir_path)
        for image in image_list:
            img = cv2.imread(image)
            # resized = cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_CUBIC)
            # print(f"===>vor upscale {img.shape}")
            # up_img = self.sr.upsample(resized)
            # up_img = self.upscale_image(resized)
            self.video.write(img)

        self.video.release()

    def async_write_video(self, dir_path) -> None:
        self.start_time = time.time()
        image_list: list[AnyStr] = self.get_images(dir_path)

        print(f"async_write_video jetzt gehts los {len(image_list)}")

        rx.from_list(image_list).pipe(
            ops.do_action(lambda x: self.readImgSubject.on_next(x)),
            ops.observe_on(self.thread_pool_scheduler)
        ).subscribe(
            on_next=lambda i: print(
                f"VIEW PROCESS async_write_video: {os.getpid()} {current_thread().name}"),
            on_error=lambda e: print(e),
            on_completed=lambda: print("from list completed")
        )

        self.thread_pool_scheduler.executor.shutdown(wait=True, cancel_futures=False)

    def terminate(self):
        self.thread_pool_scheduler.executor.shutdown(wait=True, cancel_futures=False)
        self.video.release()

        print("-------ENDE---------")
        print((time.time() - self.start_time))
