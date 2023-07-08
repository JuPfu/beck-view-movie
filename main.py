from createVideo import GenerateVideo

dir_path: str = r'/Users/jp/PycharmProjects/ic/*.jpg'

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    gv = GenerateVideo()
    gv.async_write_video(dir_path)
    # gv.write_video(dir_path)

