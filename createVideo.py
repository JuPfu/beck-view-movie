# importing libraries
import os
from typing import AnyStr

import cv2

from getSortedFilenames import get_sorted_image_files


class GenerateVideo:

    def __init__(self) -> None:
        # Checking the current directory path
        print(f"cwd={os.getcwd()}")

    def get_images(self, dir_path) -> list[AnyStr]:
        return get_sorted_image_files(dir_path)

    def upscale_image(self, img):
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        # path = "ESPCN_x3.pb"
        # sr.readModel(path)
        # sr.setModel("espcn", 3)
        # result = sr.upsample(img)

        path = "ESPCN_x2.pb"
        sr.readModel(path)
        sr.setModel("espcn", 2)  # set the model by passing the value and the upsampling ratio
        result = sr.upsample(img)  # upscale the input image
        # plt.imshow(result[:, :, ::-1])
        # plt.show()
        return result

    def write_video(self, dir_path) -> None:
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        video = cv2.VideoWriter('/Users/jp/PycharmProjects/bv-movie/output_video.mp4', fourcc, 24,
                                (3840, 2160))  # (1920, 1080))
        image_list: list[AnyStr] = self.get_images(dir_path)
        for image in image_list:
            img = cv2.imread(image)
            up_img = self.upscale_image(img)
            # print(f"write_video up_img dim={up_img.shape}")
            # plt.imshow(up_img[:, :, ::-1])
            # plt.show()
            video.write(up_img)

        video.release()
