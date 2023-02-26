from dataclasses import dataclass
import io
import logging
import re
from typing import Union, Optional

# from pydantic import BaseModel
# from pydantic.color import Color
from PIL import Image, ImageColor, ImageOps, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)


@dataclass
class ImageOptions:
    anim: Optional[bool] = True
    background: Optional[str] = None
    blur: Optional[int] = None
    brightness: Optional[float] = None

    # contrast: 
    # dpr: 
    # fit: 
    # format: 
    # gamma: 
    # gamma: 
    # gravity: 
    # metadata: 
    # quality: 
    # rotate: 
    # trim: 
    # sharpen: 
    # w: 
    # width: 
    # h: 
    # height: 
    # url: 

def get_new_dimensions(img: Image, width: int = None, height: int = None) -> tuple:
    if not width and not height:
        return img.size
    
    if width and height:
        return (width, height)
    
    orig_width, orig_height = img.size

    if width and not height:
        width_percent = width / orig_width
        height = int(orig_height * width_percent)
        return (width, height)
    
    if not width and height:
        height_percent = height / orig_height
        width = int(orig_width * height_percent)
        return (width, height)


def get_aspect_ratio_factor(width: int, height: int) -> float:
    return round(width / height, 1)


def scale_down(img: Image, width: int, height: int) -> Image:
    """
    The image is never enlarged.
    If the image is larger than given width or height, it will be resized, preserving aspect ratio.
    Otherwise its original size will be kept.

    Scenarios:
        - if all smaller dimensions -> scaled down image
        - if all larger dimensions -> original image
        - if smaller + larger dimension -> scaled down image according to smaller dimension
    
    docs: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.thumbnail
    """
    return img.copy().thumbnail((width, height))


def contain(img: Image, width: int, height: int) -> Image:
    """
    Image will be resized (shrunk or enlarged) to be as large as possible within the given
    width or height while preserving the aspect ratio.

    Scenarios:
        - all smaller dimensions -> scaled down image
        - all larger dimensions -> scaled up image
        - smaller + larger dimension -> scaled down image according to smaller dimension

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.contain
    """
    return ImageOps.contain(img, (width, height))


"""
Control the cropping position.

Use (0.5, 0.5) for center cropping
    if cropping the width (tall image), take 50% off of the left side, and therefore 50% off the right side

(0.0, 0.0) will crop from the top left corner
    if cropping the width (tall image), take all of the crop off of the right side
    if cropping the height (wide image), take all of it off the bottom
    
(1.0, 0.0) will crop from the bottom left corner, etc.
    if cropping the width (tall image), take all of the crop off the left side
    if cropping the height (wide image), take none from the top, and therefore all off the bottom

for wide images, left and right should be same as center, but its actually gravitating to top

wide, cropping height: 
    default - (0.5, 0.5)
    top - (0, 0) or (1, 0)         y coordinate same      top -    TOP_LEFT, BOTTOM_LEFT
    bottom - (1, 1) or (0, 1)      y coordinate same      bottom - BOTTOM_RIGHT, TOP_RIGHT
    left, should show same as default - (0.5, 0.5)
    right, should show same as default - (0.5, 0.5)

---------------------------

tall, cropping width:
    default - (0.5, 0.5)
    top, should be same as default - (0.5, 0.5)
    bottom - should be same as default - (0.5, 0.5)
    left - (0, 0) or (0, 1)       same x coordinate      left -  TOP_LEFT, TOP_RIGHT
    right - (1, 0) or (1, 1)      same x coordinate      right - BOTTOM_LEFT, BOTTOM_RIGHT

"""
CENTER_CROP = (0.5, 0.5)
TOP_LEFT = (0, 0)
BOTTOM_LEFT = (1, 0)
TOP_RIGHT = (0, 1)
BOTTOM_RIGHT = (1, 1)

WIDE_IMAGE_GRAVITY_OPTIONS = {
    'top': TOP_LEFT,
    'bottom': BOTTOM_RIGHT,
    'left': CENTER_CROP,
    'right': CENTER_CROP
}

TALL_IMAGE_GRAVITY_OPTIONS = {
    'top': CENTER_CROP,
    'bottom': CENTER_CROP,
    'left': TOP_LEFT,
    'right': BOTTOM_LEFT
}


def cover(img: Image, width: int, height: int, gravity: tuple = CENTER_CROP) -> Image:
    """
    Resizes (shrinks or enlarges) to fill the entire area of width and height. If the image has an aspect ratio
    different from the ratio of width and height, it will be cropped to fit.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.fit
    """
    return ImageOps.fit(img, (width, height), centering=gravity)


def crop(img: Image, width: int, height: int, gravity: tuple = CENTER_CROP) -> Image:
    """
    Image will be shrunk and cropped to fit within the area specified by width and height.
    The image will not be enlarged.

    Original dimensions are the maximum possible dimensions.

    Scenarios:
        - smaller dimensions -> scaled down image
        - larger dimensions -> original image
        - smaller + larger dimensions -> cropped image with smaller + original dimension
    
    docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.fit
    """
    orig_width, orig_height = img.size

    # Take smallest height and width
    width, height = min(orig_width, width), min(orig_height, height)

    orig_aspect_ratio = get_aspect_ratio_factor(width=orig_width, height=orig_height)
    crop_aspect_ratio = get_aspect_ratio_factor(width=width, height=height)


    # figure out how to handle gravity options for differently sized images
    if gravity is not CENTER_CROP:

        # need to fix this! decide on if gravity should be string of "top, left, bottom, etc" or Pillow tuple options
        if crop_aspect_ratio > orig_aspect_ratio:
            gravity = WIDE_IMAGE_GRAVITY_OPTIONS[gravity]
        else:
            gravity = TALL_IMAGE_GRAVITY_OPTIONS[gravity]

    return ImageOps.fit(img, (width, height), centering=gravity)


def save_image(img: Image, webp: bool = False, quality: int = 75) -> io.BytesIO:
    """
    This function should handle how to save the image by
    setting the following options:
        - correct output type (webp, avif, or original image)
        - quality (75 is Pillow's default)
    """
    pass


def fill_background_color(img: Image, color: Optional[tuple] = (0, 0, 0)) -> Optional[Image.Image]:
    if img.mode in ("RGBA", "LA"):
        background = Image.new(img.mode[:-1], img.size, color)
        background.paste(img, mask=img)
        return background


def freeze_animated_image(img: Image) -> Optional[Image.Image]:
    """
    Return the first frame of an animated image
    """
    if animated := getattr(img, "is_animated", False):
        img.seek(0)
        return img


def blur(img: Image, blur_radius: int) -> Image:
    """
    Applies Gaussian blur to image.

    Looks like blur_radius has no fixed limit according to Pillow docs,
    (ex. blur radius 300 is blurrier than blur radius 250)
    so we can just cap it at 250, similar to CloudFlare.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html#PIL.ImageFilter.GaussianBlur
    """
    return img.filter(ImageFilter.GaussianBlur(blur_radius))


def brightness(img: Image, brighten_amount: Union[float, int]) -> Image:
    """
    Applies brightness to image.

    Amount of 0 gives you a black image
    Amount of 1.0 gives you original image
    No cap

    CloudFlare doesn't have a cap on brightness.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Brightness
    """
    filter = ImageEnhance.Brightness(img)
    return filter.enhance(brighten_amount)


def contrast(img: Image, contrast_amount: Union[float, int]) -> Image:
    """
    Applies contrast to image.

    Amount of 0 gives you grey image.
    Amount of 1.0 gives you original image
    No cap

    CloudFlare doesn't have a cap on brightness.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Contrast
    """
    filter = ImageEnhance.Enhance(img)
    return filter.enhance(contrast_amount)


def read_from_bytes(img_bytes_str: bytes) -> Image:
    """
    Return a Pillow Image from bytes string.
    """

    return Image.open(io.BytesIO(img_bytes_str))


def write_to_buffer(img: Image, webp: bool = False) -> io.BytesIO:
    """
    Save Pillow Image to buffer and return buffer.

    Supports webp format.

    webp docs: https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#webp
    """
    buffer = io.BytesIO()
    format = 'webp' if webp else img.format

    img.save(buffer, format=format)

    return buffer


def is_valid_hex(hex_color: str):
    return re.search(r'^#([0-9a-fA-F]{3}){1,2}$', hex_color)


def get_rgb_from_hex(hex_color: str) -> tuple:
    return ImageColor.getrgb(hex_color)


def pad(img: Image, width: int, height: int, color: Optional[Union[str, tuple]] = (0, 0, 0)) -> Image:
    """
    Takes in background color!

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.pad
    """

    if isinstance(color, str) and is_valid_hex(color):
        color = get_rgb_from_hex(color)

    return ImageOps.pad(img, (width, height), color=color)


def gravity():
    pass


def trim():
    pass
