# beck-view-movie

[beck-view-movie](https://github.com/JuPfu/beck-view-movie) is a Python project designed to generate a movie from digitized frames (images) produced by the [beck-view-digitalize](https://github.com/JuPfu/beck-view-digitalize) project. This program converts a sequence of frames into a video file and supports parallel processing to optimize the performance when working with a large number of images.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [License](#license)

## Overview

[beck-view-movie](https://github.com/JuPfu/beck-view-movie) is the second step in the process of digitizing Super V8 films. After the frames have been digitized and stored in an output directory by the [beck-view-digitalize](https://github.com/JuPfu/beck-view-digitalize) project, this program assembles the frames into a video file. The core method of this project utilizes parallel processing for efficient handling of a large number of images.

![beck-view](./assets/img/beck-view-overview.jpg)

## Features

- Assembles digitized frames into a video file.
- Frames are sorted in the correct sequence to ensure proper chronological order in the video.
- Supports parallel processing for efficient handling of large image sets.
- Customizable frame rate (FPS) and output video file name.
- Supports batch processing, this means images are worked on in chunks - default chunk size is 100 images, to enhance performance.
- Logging for detailed information and progress tracking.
- An executable image <em>"beck-view-movie.exe"</em> can be generated with the help of Nuitka.

## Requirements

- Python 3.11 or higher
- Required Python packages:
    - `numpy`
    - `opencv-python`
    - `tqdm`
    
Ensure you have all necessary dependencies installed using the provided requirements file or installing packages via pip:

## Installation

Clone the repository:
```shell
git clone https://github.com/JuPfu/beck-view-movie
cd beck-view-movie
```

Install the required dependencies:
```shell
pip install -r requirements.txt
```
Optional - build executable <em>beck-view-movie.exe</em>:
   ```bash
   pip3 install nuitka
   pip3 install imageio

   nuitka.bat
   ```

## Usage

To use the beck-view-movie program, you must run the script from the command line and provide the necessary arguments. The program accepts the following command-line arguments:

- -p <br>Specifies the path to the directory containing PNG frames matching the pattern frame{number}.png. The default is the current directory.
```shell
-p /path/to/input/directory
```

- -o <br>Specifies the output directory where the generated MP4 movie will be saved. The default is the current directory.
```shell
-o /path/to/output/directory
```

- -n <br>Specifies the name of the output MP4 movie file without postfix. The default is "beck-view-movie".
```shell
-n output_video
```

- -of <br>Specifies the output format generated and the postfix assigned to the movie file generated. The default is "mp4". 
Allowed formats are `avi`, `mp4`, `mp4v`, `m4v` and  `wmf`. The default is  `mp4`.<br/>
Example: When `-n output_video` and `-of wmf` had  been specified,  a  movie file with the basename `output_video.wmf` will
be generated. This generated file will be in `wmf` format.
```shell
-of wmf
```

- -fps <br>Specifies the frames per second (FPS) for the video. The default is 24 FPS, and acceptable values range from 15 to 30.
```shell
-fps 21
```

- -fh <br>Flip  images horizontally.
```shell
-fh
```

- -fv <br>Flip  images vertically.
```shell
-fv
```

- -w <br>Number of parallel worker threads. The default value is 8. The value should be adapted to your  hardware. Affects speed of assembly.
```shell
-w 8
```

- -bs <br>Specifies the batch size which is worked on in parallel in each worker thread. The default is 100 frames (images).
```shell
-bs 25
```

- -wh <br>Specifies the width and height of the frames (images) in the directory designated with the `-p`option. The default is a width of 1920 and a height of 1080  pixels.
```shell
-wh 1920 1080
```


## Examples

Here's an example of how to run the program from the command line:

```shell
python beck_view_movie.py -p /path/to/input/directory -o /path/to/output/directory -n my_movie -of wmf -fps 24 -wh 1280  720
```

In this example, the program will generate a movie with the resolution of 1280 x 720 pixles in wmf format named my_movie.wmf at 24 frames per second from PNG frames in the specified input directory. The output video file will be saved to the specified output directory.

You can run the program without any arguments to use the default values for each option.

For additional help and information on usage, you can use the --help flag:

```shell
python beck_view_movie.py --help
```
This will display a usage guide with information on the available arguments and their default values.

## License

[beck-view-movie](https://github.com/JuPfu/beck-view-movie) is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Information
This `README.md` file provides information on the project, its features, requirements, installation, usage, and examples. It is a comprehensive guide for anyone who wants to understand and use the [beck-view-movie](https://github.com/JuPfu/beck-view-movie) project. Let me know if you need any further assistance or adjustments!
