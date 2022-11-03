import glob
import os
from PIL import Image


def get_image_files(path):
    types = ('*.jpg', '*.JPG', '*.jpeg', '*.JPEG', '*.png', '*.PNG' '*.webp', '*.WEBP')
    filepaths = []
    filenames = []
    for type in types:
        filepaths.extend(glob.glob(path + '/' + type))

    filepaths = sorted(filepaths)

    for file in filepaths:
        head, tail = os.path.split(file)
        filenames.append(tail)


    return tuple(zip(filenames, filepaths))

def save_image_to_file(image: Image, filepath=None)
    create_folder(filepath)
    
    

def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)
