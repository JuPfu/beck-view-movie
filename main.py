from createVideo import GenerateVideo

dir_path: str = r'/Users/jp/PycharmProjects/beck-view-digitalize/film/frame*.png'
# dir_path: str = r'/Users/jp/PycharmProjects/beck-view-digitalize/frame*.png'
# dir_path: str = r'/Users/jp/Downloads/Gerald/*.jpg'

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    generate_video = GenerateVideo()
    generate_video.write_video(dir_path)
    # gv.write_video(dir_path)
