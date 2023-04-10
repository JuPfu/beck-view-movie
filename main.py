from createVideo import GenerateVideo

dir_path = r'/Users/jp/Downloads/beck/*.jpg'

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    gv = GenerateVideo()
    gv.write_video(dir_path)
