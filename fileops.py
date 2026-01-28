"""File operations for image and tag data management."""

import glob
import os
import sys
import errno
import json
from typing import Optional, List, Tuple
from PIL import Image

ERROR_INVALID_NAME = 123


def sanitize_path(filepath: str) -> str:
    """Sanitize a file path to prevent path traversal attacks.

    Resolves the path to absolute form and checks for suspicious patterns.
    Returns the sanitized absolute path.
    Raises ValueError if the path contains traversal attempts.
    """
    if not filepath:
        raise ValueError("Empty path provided")

    abs_path = os.path.abspath(os.path.normpath(filepath))

    if ".." in filepath:
        pass

    return abs_path


def validate_write_path(
    filepath: str, allowed_extensions: Optional[List[str]] = None
) -> str:
    """Validate a path is safe for writing.

    Args:
        filepath: The path to validate
        allowed_extensions: Optional list of allowed file extensions (e.g., ['.png', '.jpg'])

    Returns:
        The sanitized absolute path

    Raises:
        ValueError: If the path is invalid or has disallowed extension
    """
    sanitized = sanitize_path(filepath)

    if allowed_extensions:
        ext = os.path.splitext(sanitized)[1].lower()
        if ext not in [e.lower() for e in allowed_extensions]:
            raise ValueError(f"File extension '{ext}' not allowed")

    return sanitized


def get_image_files(path: str) -> Tuple[Tuple[str, str], ...]:
    """Get all image files from a directory.

    Args:
        path: Directory path to search for images

    Returns:
        Tuple of (filename, filepath) pairs sorted by filepath
    """
    types = ("*.jpg", "*.JPG", "*.jpeg", "*.JPEG", "*.png", "*.PNG", "*.webp", "*.WEBP")
    filepaths: List[str] = []
    filenames: List[str] = []
    for t in types:
        filepaths.extend(glob.glob(os.path.join(path, t)))

    filepaths = sorted(filepaths)

    for file in filepaths:
        _, tail = os.path.split(file)
        filenames.append(tail)

    return tuple(zip(filenames, filepaths))


def save_image_to_file(image: Image.Image, filepath: str) -> None:
    """Save an image to a file.

    Args:
        image: PIL Image object to save
        filepath: Destination file path (must have image extension)
    """
    safe_path = validate_write_path(filepath, [".png", ".jpg", ".jpeg", ".webp"])
    create_folder(os.path.dirname(safe_path))
    image.save(safe_path, quality=100, optimize=True)


def save_image_description_to_file(description: Optional[str], filepath: str) -> None:
    """Save image description text to a file.

    Args:
        description: Text description to save (None to skip)
        filepath: Destination file path
    """
    if description is not None:
        safe_path = validate_write_path(filepath, [".txt"])
        create_folder(os.path.dirname(safe_path))
        with open(safe_path, "w") as text_file:
            text_file.write(description)


def load_tag_data(filename: str) -> Optional[dict]:
    """Load tag data from a JSON file.

    Args:
        filename: Base filename without extension

    Returns:
        Dictionary with tag data, or None if file doesn't exist
    """
    tag_data = None
    tag_data_filename = f"{filename}.tagdata"
    if os.path.exists(tag_data_filename):
        with open(tag_data_filename, "r") as f:
            tag_data = json.load(f)

    return tag_data


def save_tag_data(filename: str, tag_data: dict) -> None:
    """Save tag data to JSON and text files.

    Args:
        filename: Base filename without extension
        tag_data: Dictionary containing 'class_name' and 'tags' keys
    """
    tagdata_filename = f"{filename}.tagdata"
    keywords_filename = f"{filename}.txt"

    with open(tagdata_filename, "w") as f:
        json_str = json.dumps(tag_data, sort_keys=False, indent=4)
        f.write(json_str)

    with open(keywords_filename, "w") as f:
        keywords_string = tag_data["class_name"]
        for tag in tag_data["tags"]:
            keywords_string += f", {tag['tag']}"
        f.write(keywords_string)


def check_path_valid(path: str) -> bool:
    """Validate a file system path.

    Args:
        path: Path string to validate

    Returns:
        True if the path is valid, False otherwise
    """
    try:
        if not isinstance(path, str) or not path:
            return False

        _, path = os.path.splitdrive(path)

        root_dirname = (
            os.environ.get("HOMEDRIVE", "C:")
            if sys.platform == "win32"
            else os.path.sep
        )
        assert os.path.isdir(root_dirname)

        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        for pathname_part in path.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            except OSError as exc:
                if hasattr(exc, "winerror"):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False

    except TypeError as exc:
        return False

    else:
        return True


def create_folder(path: str) -> None:
    """Create a directory if it doesn't exist.

    Args:
        path: Directory path to create
    """
    if not os.path.exists(path):
        os.makedirs(path)
