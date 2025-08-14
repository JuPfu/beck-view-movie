import logging
import os
import pathlib
import sys
from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from random import randint
from typing import List

import cv2
import numpy as np
from numpy import ndarray
from tqdm import tqdm

from getSortedFilenames import get_sorted_image_files
from tqdm_logger import TqdmLogger


class GenerateVideo:

    def __init__(self, args: Namespace) -> None:
        self.calibrate_debevec: cv2.CalibrateDebevec
        self.merge_debevec: cv2.MergeDebevec
        self.tone_map = cv2.TonemapDrago

        self._initialize_args(args)
        self._initialize_logging()
        self._initialize_resolution()
        if self.bracketing: self._initialize_bracketing()
        self._initialize_video_writer()

    def _initialize_args(self, args: Namespace) -> None:
        self.path: pathlib.Path = args.path
        self.opath: pathlib.Path = args.opath
        self.name: str = os.path.splitext(args.name)[0]
        self.output_format: str = args.output_format
        self.fps: float = args.fps
        self.batch_size: int = min(max(1, args.batch_size), 498)
        self.bracketing: bool = args.bracketing
        self.tone_mapper_preset = getattr(args, "tone_mapper_preset", "default").lower()
        self.tone_mapper: str = getattr(args, "tone_mapper", "drago").lower()

        self.left_crop = 230
        self.right_crop = 230

        if self.bracketing:
            self.batch_size = min(max(3, self.batch_size - (self.batch_size % 3)), 498)

        self._apply_tone_mapper_preset()

        # Allow overrides
        self.drago_bias = getattr(args, "drago_bias", self.drago_bias)
        self.reinhard_gamma = getattr(args, "reinhard_gamma", self.reinhard_gamma)
        self.reinhard_intensity = getattr(args, "reinhard_intensity", self.reinhard_intensity)
        self.reinhard_light_adapt = getattr(args, "reinhard_light_adapt", self.reinhard_light_adapt)
        self.reinhard_color_adapt = getattr(args, "reinhard_color_adapt", self.reinhard_color_adapt)
        self.mantiuk_scale = getattr(args, "mantiuk_scale", self.mantiuk_scale)
        self.mantiuk_saturation = getattr(args, "mantiuk_saturation", self.mantiuk_saturation)
        self.mantiuk_bias = getattr(args, "mantiuk_bias", self.mantiuk_bias)

        self.num_workers: int = args.num_workers
        self.width_height = args.width_height
        self.codec: str = args.codec

        self.flip: int = 2  # no flip

        if args.flip_horizontal:
            self.flip = 0

        if args.flip_vertical:
            self.flip = 1

        if args.flip_horizontal and args.flip_vertical:
            self.flip = -1

        self.gui = args.gui

    def _apply_tone_mapper_preset(self) -> None:
        self.drago_bias = 2.2
        self.reinhard_gamma = 1.0
        self.reinhard_intensity = 0.0
        self.reinhard_light_adapt = 1.0
        self.reinhard_color_adapt = 0.0
        self.mantiuk_scale = 1.0
        self.mantiuk_saturation = 1.0
        self.mantiuk_bias = 1.0

        if self.tone_mapper_preset == "cinematic":
            self.tone_mapper = "mantiuk"
            self.mantiuk_scale = 0.9
            self.mantiuk_saturation = 1.3
            self.mantiuk_bias = 1.0

        elif self.tone_mapper_preset == "natural":
            self.tone_mapper = "reinhard"
            self.reinhard_gamma = 1.2
            self.reinhard_intensity = 0.0
            self.reinhard_light_adapt = 1.0
            self.reinhard_color_adapt = 0.2

        elif self.tone_mapper_preset == "highlight":
            self.tone_mapper = "drago"
            self.drago_bias = 1.0

        elif self.tone_mapper_preset == "soft":
            self.tone_mapper = "reinhard"
            self.reinhard_gamma = 1.1
            self.reinhard_intensity = -0.3
            self.reinhard_light_adapt = 0.9
            self.reinhard_color_adapt = 0.3

        elif self.tone_mapper_preset == "vivid":
            self.tone_mapper = "mantiuk"
            self.mantiuk_scale = 1.0
            self.mantiuk_saturation = 1.5
            self.mantiuk_bias = 1.1

        elif self.tone_mapper_preset == "neutral":
            self.tone_mapper = "drago"
            self.drago_bias = 2.0

    def _initialize_logging(self) -> None:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        if self.gui:
            handler = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(handler)

    def _initialize_resolution(self) -> None:
        self.image_list: List[str] = get_sorted_image_files(self.bracketing, str(self.path))

        self.width = 1920
        self.height = 1080
        if self.width_height != "automatic":
            self.wh: List[str] = self.width_height.split("x")
            self.width: int = int(self.wh[0]) if int(self.wh[0]) >= 100 else 1920
            self.height: int = int(self.wh[1]) if int(self.wh[1]) >= 100 else 1080
        else:
            index: int = randint(0, len(self.image_list) - 1)
            test_image = cv2.imread(self.image_list[index])
            (self.height, self.width, _) = test_image.shape

        self.logger.info(
            f"Creating video from {len(self.image_list)} 'frames*.png' files with resolution {self.width} x {self.height} in {str(self.opath / self.name)}.{self.output_format}.")
    def _initialize_bracketing(self) -> None:
        self.times: ndarray[np.float32] = np.asarray([128.0, 256.0, 64.0], dtype=np.float32)
        self.calibrate_debevec = cv2.createCalibrateDebevec()
        self.merge_debevec = cv2.createMergeDebevec()

        self.logger.info(f"Tone mapper preset: {self.tone_mapper_preset} using: {self.tone_mapper}")

        if self.tone_mapper == "drago":
            self.logger.info(f"Using TonemapDrago (bias={self.drago_bias})")
            self.tone_map = cv2.createTonemapDrago(self.drago_bias)

        elif self.tone_mapper == "reinhard":
            self.logger.info(
                f"Using TonemapReinhard (gamma={self.reinhard_gamma}, intensity={self.reinhard_intensity}, light_adapt={self.reinhard_light_adapt}, color_adapt={self.reinhard_color_adapt})")
            self.tone_map = cv2.createTonemapReinhard(self.reinhard_gamma, self.reinhard_intensity,
                                                      self.reinhard_light_adapt, self.reinhard_color_adapt)

        elif self.tone_mapper == "mantiuk":
            self.logger.info(
                f"Using TonemapMantiuk (scale={self.mantiuk_scale}, saturation={self.mantiuk_saturation}, bias={self.mantiuk_bias})")
            self.tone_map = cv2.createTonemapMantiuk(self.mantiuk_scale, self.mantiuk_saturation, self.mantiuk_bias)

        else:
            raise ValueError(f"Unknown tone mapper: {self.tone_mapper}")

    def _initialize_video_writer(self) -> None:
        resolution = (self.width, self.height)
        fourcc = cv2.VideoWriter.fourcc(*self.codec)
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name) + "." + self.output_format,
                                            fourcc=fourcc,
                                            fps=self.fps,
                                            frameSize=resolution)

    def _preload_image_groups(self, grouped_paths: List[List[str]]) -> List[List[ndarray]]:
        def load_group(paths: List[str]) -> List[ndarray]:
            images = []
            for path in paths:
                img = cv2.imread(path, cv2.IMREAD_COLOR)
                if img is None:
                    raise ValueError(f"Failed to load image: {path}")
                img = cv2.flip(img, self.flip) if self.flip != 2 else img

                # Crop out black borders before HDR merge
                # Assume 16mm image center is ~10.3:7.5 inside 1920x1080
                # Calculate crop dynamically if desired, or hardcode for now:
                if self.bracketing:
                    img = img[:, self.left_crop: img.shape[1] - self.right_crop]

                images.append(img)

            return images

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            return list(executor.map(load_group, grouped_paths))

    # see https://www.toptal.com/opencv/python-image-processing-in-computational-photography
    # method can be removed if results are not satisfying
    # this method removes intensities that are represented in very few pixels
    def countTonemap(self, hdr: ndarray[np.float32], min_fraction=0.0005) -> ndarray[np.float32]:
        counts, ranges = np.histogram(hdr, 256)
        min_count = min_fraction * hdr.size
        delta_range = ranges[1] - ranges[0]

        image = hdr.copy()
        for i in range(len(counts)):
            if counts[i] < min_count:
                image[image >= ranges[i + 1]] -= delta_range
            ranges -= delta_range

        normalized_image = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

        return normalized_image

    def process_batch(self, image_paths: List[str]) -> List[ndarray]:
        def group(sequence, chunk_size) -> List[List[str]]:
            return [sequence[i:i + chunk_size] for i in range(0, len(sequence), chunk_size)]

        group_size = 3 if self.bracketing else 1
        grouped_paths: List[List[str]] = group(image_paths, group_size)

        preloaded_images: List[List[ndarray]] = self._preload_image_groups(grouped_paths)

        def process(images: List[ndarray]) -> ndarray:
            if not self.bracketing:
                return images[0]
            response = self.calibrate_debevec.process(images, self.times)
            hdr = self.merge_debevec.process(images, self.times, response)
            hdr_normalized = self.countTonemap(hdr, min_fraction=0.0005)
            ldr = self.tone_map.process(hdr_normalized)

            # Pad back to 1920x1080
            if self.bracketing:
                ldr = cv2.copyMakeBorder(
                    ldr,
                    top=0,
                    bottom=0,
                    left=self.left_crop,
                    right=self.right_crop,
                    borderType=cv2.BORDER_REFLECT_101,
                    value=(0, 0, 0)  # Black padding
                )

            return (ldr * 256).astype(dtype=np.uint8)

        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            return list(executor.map(process, preloaded_images))

    def assemble_video(self) -> None:
        if self.gui:
            progress_bar = tqdm(range(0, len(self.image_list), self.batch_size), unit_scale=self.batch_size,
                                desc="Generation progress", unit="frames", file=TqdmLogger(self.logger), mininterval=5)
        else:
            progress_bar = tqdm(range(0, len(self.image_list), self.batch_size), unit_scale=self.batch_size,
                                desc="Generation progress", unit="frames")

        for start in progress_bar:
            end: int = start + self.batch_size
            batch = self.image_list[start:end]

            processed_images = self.process_batch(batch)

            for img in processed_images:
                self.video_writer.write(img)
                del img

        # Log completion
        self.logger.info(f"Video {str(self.opath / self.name)}.{self.output_format} assembled successfully.")

    def __del__(self) -> None:
        if hasattr(self, "video_writer"):
            self.video_writer.release()
