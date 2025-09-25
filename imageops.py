from PIL import Image, ImageTk


def load_image(path):
    return Image.open(path)

def crop_image(image: Image, scale_ratio, box):
    scaled_box = (
    int(box[0] / scale_ratio), int(box[1] / scale_ratio), int(box[2] / scale_ratio), int(box[3] / scale_ratio))
    return image.crop(scaled_box)

def resize_image(image: Image, width=None, height=None):
    if height is None and width is not None:
        height = image.height * width // image.width
    elif width is None and height is not None:
        width = image.width * height // image.height
    elif height is None and width is None:
        raise RuntimeError("At lease one of width and height must be present")
    return image.resize((width, height), Image.LANCZOS)
    
def rotate_image(image, angle):
        return image.rotate(angle, Image.BICUBIC, expand=True)

def scale_image(image: Image, ratio=None):
    return image.resize((int(image.width * ratio), int(image.height * ratio)), Image.LANCZOS)
