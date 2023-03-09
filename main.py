from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import io
import logging
import re
from typing import Union, Optional, Literal
from pathlib import Path

# from pydantic import BaseModel
# from pydantic.color import Color
from PIL import Image, ImageColor, ImageOps, ImageFilter, ImageEnhance

logger = logging.getLogger(__name__)



def round_up(value):
    rounded = Decimal(value).quantize(1, rounding=ROUND_HALF_UP)
    return int(rounded)


def get_filename_stem(name: str) -> str:
    return Path(name).stem


# def get_new_dimensions(img: Image, width: int = None, height: int = None) -> tuple:
#     """
#     Return new dimensions given original image's aspect ratio and a width or height.
#     """
#     if not width and not height:
#         return img.size
    
#     if width and height:
#         return (width, height)
    
#     orig_width, orig_height = img.size

#     if width and not height:
#         width_percent = width / orig_width
#         height = int(orig_height * width_percent)
#         return (width, height)
    
#     if not width and height:
#         height_percent = height / orig_height
#         width = int(orig_width * height_percent)
#         return (width, height)

def get_new_dimensions(img: Image, width: int = None, height: int = None) -> tuple:
    """
    Return new dimensions given original image's aspect ratio and a width or height.
    """

    if not width and not height:
        return img.size

    if width and height:
        return (width, height)
    
    orig_width, orig_height = img.size

    # calculate new height
    if width and not height:
        height = round_up((orig_height / orig_width) * width)
        return (width, height)
    
    # calculate new width
    if not width and height:
        width = round_up((orig_width / orig_height) * height)
        return (width, height)


def get_aspect_ratio_factor(width: int, height: int) -> float:
    """
    Calculate aspect ratio factor of an image.
    """
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
    img.thumbnail((width, height))
    return img


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

# WIDE_IMAGE_GRAVITY_OPTIONS = {
#     'top': TOP_LEFT,
#     'bottom': BOTTOM_RIGHT,
#     'left': CENTER_CROP,
#     'right': CENTER_CROP
# }

# TALL_IMAGE_GRAVITY_OPTIONS = {
#     'top': CENTER_CROP,
#     'bottom': CENTER_CROP,
#     'left': TOP_LEFT,
#     'right': BOTTOM_LEFT
# }

def cover(img: Image, width: int, height: int, gravity: tuple = CENTER_CROP) -> Image:
    """
    Resizes (shrinks or enlarges) to fill the entire area of width and height. If the image has an aspect ratio
    different from the ratio of width and height, it will be cropped to fit.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.fit
    """
    return ImageOps.fit(img, (width, height), centering=gravity)


class Gravity(Enum):
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"

CENTER_CROP = (0.5, 0.5)
TOP_LEFT = (0, 0)
BOTTOM_LEFT = (1, 0)
TOP_RIGHT = (0, 1)
BOTTOM_RIGHT = (1, 1)

# cropping height
WIDE_IMAGE_GRAVITY_OPTIONS = {
    Gravity.TOP: TOP_LEFT,
    Gravity.BOTTOM: BOTTOM_RIGHT,
    Gravity.LEFT: CENTER_CROP,
    Gravity.RIGHT: CENTER_CROP
}

# cropping width
TALL_IMAGE_GRAVITY_OPTIONS = {
    Gravity.TOP: CENTER_CROP,
    Gravity.BOTTOM: CENTER_CROP,
    Gravity.LEFT: TOP_LEFT,
    Gravity.RIGHT: BOTTOM_LEFT
}

def get_centering_from_gravity(img: Image, width: int, height: int, gravity: Gravity) -> tuple:
    """
    Return the Pillow centering tuple based on gravity option
    and aspect ratio of new image.  
    """

    orig_aspect_ratio = get_aspect_ratio_factor(width=img.size[0], height=img.size[1])
    new_aspect_ratio = get_aspect_ratio_factor(width=width, height=height)

    if gravity is Gravity.CENTER:
        return CENTER_CROP

    if new_aspect_ratio > orig_aspect_ratio:
        return WIDE_IMAGE_GRAVITY_OPTIONS[gravity]
    else:
        return TALL_IMAGE_GRAVITY_OPTIONS[gravity]


def crop(img: Image, width: int, height: int, gravity: Gravity = Gravity.CENTER) -> Image:
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

    # Get Pillow centering position from gravity
    centering = get_centering_from_gravity(img=img, width=width, height=height, gravity=gravity)

    # orig_aspect_ratio = get_aspect_ratio_factor(width=orig_width, height=orig_height)
    # crop_aspect_ratio = get_aspect_ratio_factor(width=width, height=height)

    # # figure out how to handle gravity options for differently sized images
    # if gravity is not CENTER_CROP:

    #     # need to fix this! decide on if gravity should be string of "top, left, bottom, etc" or Pillow tuple options
    #     if crop_aspect_ratio > orig_aspect_ratio:
    #         gravity = WIDE_IMAGE_GRAVITY_OPTIONS[gravity]
    #     else:
    #         gravity = TALL_IMAGE_GRAVITY_OPTIONS[gravity]

    return ImageOps.fit(img, (width, height), centering=centering)


def rotate(img: Image, degrees: int) -> Image:
    """
    Return a rotated version of the image.
    Valid rotation degrees are 90, 180, or 270.

    docs: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.rotate
    """
    return img.rotate(angle=degrees, expand=True)


@dataclass
class TrimPixels:
    top: int = 0
    bottom: int = 0
    left: int = 0
    right: int = 0


def trim(img: Image, trim: TrimPixels) -> Image:
    """
    Cut off pixels from an image.
    TODO: Perform validation to make sure we're pixels don't exceed image dimensions.
    """
    width, height = img.size
    dimensions = (trim.left, trim.top, width-trim.right, height-trim.bottom)

    return img.crop(box=dimensions)


def strip_exif_data(img: Image) -> None:
    """
    Removes image EXIF metadata if it exists.
    """
    if 'exif' in img.info:
        del img.info['exif']


def sharpen(img: Image, sharpen_amount: Union[float, int]) -> Image:
    """
    Adjust image sharpness.

    CloudFlare
        - 0 (no sharpening, default)
        - 10 (maximum)
        - 1 is a recommended value for downscaled images
    will error if value not between 0 - 10 inclusive

    Pillow
        - factor of 0.0 gives a blurred image
        - a factor of 1.0 gives the original image
        - a factor of 2.0 gives a sharpened image
        - has no cap, but we can enforce a cap at 10?

    Proposed:
        - 0 (no sharpening, default)
        - 10 (maximum)

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Sharpness
    """
    filter = ImageEnhance.Sharpness(img)
    return filter.enhance(sharpen_amount)


def save_image(img: Image, webp: bool = False, quality: int = 75) -> io.BytesIO:
    """
    This function should handle how to save the image by
    setting the following options:
        - correct output type (webp, avif, or original image)
        - quality (75 is Pillow's default)
        - optimize for non-webp formats (because optimize doesn't benefit webp)
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


def blur(img: Image, blur_radius: Union[float, int]) -> Image:
    """
    Applies Gaussian blur to image.

    Looks like blur_radius has no fixed limit according to Pillow docs,
    (ex. blur radius 300 is blurrier than blur radius 250)
    so we can just cap it at 250, similar to CloudFlare.

    CloudFlare range: 1 - 250 inclusive. Anything below 1 is ignored.

    Pillow < 1 values do blur.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html#PIL.ImageFilter.GaussianBlur
    """
    return img.filter(ImageFilter.GaussianBlur(blur_radius))


def brightness(img: Image, brighten_amount: Union[float, int]) -> Image:
    """
    Applies brightness to image.

    Amount of 0 gives you a black image
    Amount of 1.0 gives you original image
    No cap.

    CloudFlare range: 0 - 255 inclusive.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Brightness
    """
    # Reset brightness if its 0 to avoid black image.
    brighten_amount = 1 if brighten_amount == 0 else brighten_amount
    filter = ImageEnhance.Brightness(img)
    return filter.enhance(brighten_amount)


def contrast(img: Image, contrast_amount: Union[float, int]) -> Image:
    """
    Applies contrast to image.

    Amount of 0 gives you a greyed out image.
    Amount of 1.0 gives you original image
    No cap.

    CloudFlare range: 0 - 255 inclusive.

    docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Contrast
    """
    # Reset contrast if its 0 to avoid 
    contrast_amount = 1 if contrast_amount == 0 else contrast_amount
    filter = ImageEnhance.Contrast(img)
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
