"""Image processing operations."""

from PIL import Image, ImageTk


def load_image(path):
    """Load an image from a file."""
    with Image.open(path) as img:
        return img.copy()

def crop_image(image: Image, scale_ratio, box):
    """Crop an image using a bounding box."""
    scaled_box = (
    int(box[0] / scale_ratio), int(box[1] / scale_ratio), int(box[2] / scale_ratio), int(box[3] / scale_ratio))
    return image.crop(scaled_box)

def resize_image(image: Image, width=None, height=None):
    """Resize an image to specified dimensions."""
    if height is None and width is not None:
        height = image.height * width // image.width
    elif width is None and height is not None:
        width = image.width * height // image.height
    elif height is None and width is None:
        raise RuntimeError("At lease one of width and height must be present")
    return image.resize((width, height), Image.LANCZOS)

def rotate_image(image, angle):
    """Rotate an image by specified angle."""
    return image.rotate(angle, Image.BICUBIC, expand=True)

def scale_image(image: Image, ratio=None):
    """Scale an image by a ratio."""
    return image.resize((int(image.width * ratio), int(image.height * ratio)), Image.LANCZOS)
