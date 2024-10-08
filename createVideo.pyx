# distutils: define_macros=NPY_NO_DEPRECATED_API=NPY_1_7_API_VERSION

# cython: language_level=3
# cython: boundscheck=False, wraparound=False, initializedcheck=False, infer_types=True
import cython

import numpy as np
cimport numpy as np
from libc.stdint cimport uint8_t  # Use C types for better performance

import logging
import os
from argparse import Namespace
from typing import List

import cv2
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor  # Ensure this is imported

from getSortedFilenames import get_sorted_image_files

cdef class GenerateVideo:
    cdef int width, height, flip, num_workers, batch_size
    cdef float fps
    cdef str name, output_format
    cdef object video_writer, path, opath, logger

    def __init__(self, args: Namespace) -> None:
        """
        Initialize the GenerateVideo class.
        """
        self._initialize_args(args)
        self._initialize_logging()
        self._initialize_video_writer()

    cdef void _initialize_args(self, object args):
        """
        Initialize the video generation arguments.
        """
        self.path = args.path
        self.opath = args.opath
        self.name = os.path.splitext(args.name)[0]
        self.output_format = args.output_format
        self.fps = args.fps
        self.batch_size = min(max(1, args.batch_size), 500)
        self.num_workers = args.num_workers
        self.width, self.height = args.width_height

        if self.width < 100 or self.height < 100:
            self.width = 1920
            self.height = 1080

        # Determine the flip mode
        self.flip = 2  # No flip by default
        if args.flip_horizontal and args.flip_vertical:
            self.flip = -1
        elif args.flip_horizontal:
            self.flip = 0
        elif args.flip_vertical:
            self.flip = 1

    cdef void _initialize_logging(self):
        """
        Initialize logging configuration.
        """
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    cdef void _initialize_video_writer(self):
        """
        Initialize the video writer.
        """
        # self.logger.info(f"Build details: {cv2.getBuildInformation()}")
        # windows specific notes
        #   output format changes with filename extension
        #   successfully tested postfixes without checking of actual coding in generated files
        #   avi
        #   mp4
        #   mp4v
        #   m4v
        #   wmv
        fourcc: int = cv2.VideoWriter.fourcc('m', 'p', '4', 'v')
        self.video_writer = cv2.VideoWriter(str(self.opath / self.name) + "." + self.output_format,
                                            fourcc=fourcc,
                                            fps=self.fps,
                                            frameSize=(self.width, self.height))

    cpdef np.ndarray process_image(self, str img_path):
        """
        Process a single image by reading and flipping.

        Args:
            img_path (str): Path to the image file.

        Returns:
            np.ndarray: Processed image.
        """
        cdef np.ndarray img
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)  # Read image as uint8
        if self.flip != 2:
            img = cv2.flip(img, self.flip)
        return img

    cpdef list process_batch(self, List[str] image_paths):
        """
        Process a batch of images in parallel.

        Args:
            image_paths (List[str]): List of image file paths.

        Returns:
            List of processed images.
        """
        # Thread pool for parallel image processing
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Use map to process images in parallel and maintain order
            processed_images = list(executor.map(self.process_image, image_paths))
        return processed_images

    cpdef void assemble_video(self, str path):
        """
        Assemble video from images using parallel processing.

        Args:
            path (str): Directory containing image files.
        """
        cdef List[str] image_list = get_sorted_image_files(path)
        cdef int start, end, total_images

        total_images = len(image_list)
        self.logger.info(f"Creating video from {total_images} 'frames*.png' files in {str(self.opath / self.name) + '.' + self.output_format}.")

        # Process images in chunks
        for start in tqdm(range(0, total_images, self.batch_size), unit_scale=self.batch_size, desc="Generation progress", unit="frames"):
            end = min(start + self.batch_size, total_images)
            batch = image_list[start:end]

            # Process and write images in batches
            processed_images = self.process_batch(batch)

            # Use a regular loop for writing, as writing requires the GIL
            for img in processed_images:
                self.video_writer.write(img)

        self.logger.info(f"Video {str(self.opath / self.name) + '.' + self.output_format} assembled successfully.")

    def __del__(self) -> None:
        """
        Destructor to release resources.
        """
        if hasattr(self, "video_writer"):
            self.video_writer.release()
