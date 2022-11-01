from PIL import Image, ImageTk


def load_image(path):
    return Image.open(path)


def crop_image():
    return 1


def resize_image(image: Image, width=None, height=None):
    if height is None and width is not None:
        height = image.height * width // image.width
    elif width is None and height is not None:
        width = image.width * height // image.height
    elif height is None and width is None:
        raise RuntimeError("At lease one of width and height must be present")
    return image.resize((width, height), Image.ANTIALIAS)
    
def scale_image(image: Image, ratio=None):
    return image.resize((int(image.width*ratio), int(image.height*ratio)), Image.ANTIALIAS)
    

def save_image():
    return 0
