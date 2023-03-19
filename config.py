from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from functools import cached_property
import io

from PIL import Image, ImageColor, ImageOps, ImageFilter, ImageEnhance, GifImagePlugin
from typing import ClassVar, Optional, Union, Literal

from pydantic import (
    BaseModel,
    Field,
    validator,
    root_validator,
    ValidationError,
    conint,
    confloat,
    NonNegativeInt,
    NonNegativeFloat,
    PrivateAttr
)
from pydantic.color import Color

from utils import get_filename_extension, get_filename_stem


# Required in order to save gifs to webp with transparency correctly!
GifImagePlugin.LOADING_STRATEGY = GifImagePlugin.LoadingStrategy.RGB_ALWAYS


class GravityEnum(str, Enum):
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class FitEnum(str, Enum):
    SCALE_DOWN = "scale_down"
    CONTAIN = "contain"
    COVER = "cover"
    CROP = "crop"
    PAD = "pad"


CENTER_CROP = (0.5, 0.5)
TOP_LEFT = (0, 0)
BOTTOM_LEFT = (1, 0)
TOP_RIGHT = (0, 1)
BOTTOM_RIGHT = (1, 1)

# cropping height
WIDE_IMAGE_GRAVITY_OPTIONS = {
    GravityEnum.TOP: TOP_LEFT,
    GravityEnum.BOTTOM: BOTTOM_RIGHT,
    GravityEnum.LEFT: CENTER_CROP,
    GravityEnum.RIGHT: CENTER_CROP
}

# cropping width
TALL_IMAGE_GRAVITY_OPTIONS = {
    GravityEnum.TOP: CENTER_CROP,
    GravityEnum.BOTTOM: CENTER_CROP,
    GravityEnum.LEFT: TOP_LEFT,
    GravityEnum.RIGHT: BOTTOM_LEFT
}


class TrimPixels(BaseModel):  # round floats?
    top: NonNegativeInt = Field(default=0)
    right: NonNegativeInt = Field(default=0)
    bottom: NonNegativeInt = Field(default=0)
    left: NonNegativeInt = Field(default=0)

    def __bool__(self):
        return any(self.dict().values())

# fit: Optional[Literal["scale_down", "contain", "cover", "crop", "pad"]] = "scale_down"
# gravity=Optional[Literal["center", "top", "bottom", "left", "right"]] = "center"

class Foo(BaseModel):
    a: Optional[int] = Field(None, ge=1, le=10)
    b: Optional[conint(ge=1, le=10)]
    c: conint(ge=1, le=10) = Field(None)
    d: conint(ge=1, le=10) = Field(8)
    e: Optional[confloat(ge=1, le=10)]
    f: confloat(ge=1, le=10) = Field(default=None)
    # c: NonNegativeInt

def round_up(value):
    return int(Decimal(value).quantize(1, rounding=ROUND_HALF_UP))


class ImageOptions(BaseModel):
    anim: Optional[bool] = True
    # enable_webp: Optional[bool] = True
    background: Optional[Color] = None

    blur: Optional[confloat(ge=0, le=255)]
    brightness: Optional[confloat(ge=0, le=255)]
    contrast: Optional[confloat(ge=0, le=255)]

    width: Optional[Union[NonNegativeFloat, NonNegativeInt]]
    height: Optional[Union[NonNegativeFloat, NonNegativeInt]]
    w: Optional[Union[NonNegativeFloat, NonNegativeInt]]
    h: Optional[Union[NonNegativeFloat, NonNegativeInt]]

    fit: Optional[FitEnum] = FitEnum.SCALE_DOWN
    gravity: Optional[GravityEnum] = GravityEnum.CENTER

    dpr: Optional[conint(ge=1, le=3)]
    metadata: Optional[bool] = False
    quality: conint(ge=0, le=100) = Field(default=80)  # has some PNG caveat with PNG8 color palette  # should we stick with 85 - CloudFlare's defaults?
    rotate: Optional[conint(multiple_of=90)]
    sharpen: Optional[confloat(ge=0, le=10)]
    # trim: Optional[TrimPixels]
    trim: Optional[str] = '0,0,0,0'

    @validator('trim', always=True)
    def save_trim_to_model(cls, values):
        """
        Convert list of strings into a `TrimPixels` instance.

        Example:
            - "1,2,3,4"          TrimPixels(top=1, right=2, bottom=3, left=4)
            - "1.1, 2.5, 3, 4"   TrimPixels(top=1, right=2, bottom=3, left=4)
        """
        # # for FastAPI to not continue running validator when no field passed
        # if values is None:
        #     return None
        try:
            pixels: list = values.replace(' ', '').split(',')
            trim_values = [round_up(float(x)) for x in pixels if x]
        except:
            raise ValueError('must be list of integer or float values')

        trim_obj = TrimPixels(
            top=trim_values[0],
            right=trim_values[1],
            bottom=trim_values[2],
            left=trim_values[3]
        )

        return trim_obj

    @root_validator
    def normalize_width_and_height(cls, values):
        """
        Make sure `width` and `height` are always populated
        and takes precedence over `w` and `h`.

        Round up width and height values.
        """
        width = values.get("width") or values.get("w")
        width = round_up(width) if width else None
        values["w"] = values["width"] = width

        height = values.get("height") or values.get("h")
        height = round_up(height) if height else None
        values["h"] = values["height"] = height

        return values

    @root_validator
    def ignore_if_width_or_height_does_not_exist(cls, values):
        """
        Set certain options to None if width or height does not exist.
        """
        width, height = values.get('width'), values.get('height')

        if not (width or height):
            for option in ['dpr', 'fit']:
                values[option] = None

        return values

    @property
    def prepared_width(self):
        if self.dpr:
            return self.width * self.dpr

        return self.width

    @property
    def prepared_height(self):
        if self.dpr:
            return self.height * self.dpr

        return self.height

i = ImageOptions(anim='true', background='black', blur=20, rotate=180, w=90, trim='1.5,2,3,4')
# i = ImageOptions(w=90, dpr=2)


@dataclass
class ImageTransformer:
    config: ImageOptions
    img: Image
    transformed_filename: str  # normalized image uri
    file_extension: Optional[str] = None
    save_options: dict = field(default_factory=dict)

    def __post_init__(self):
        """
        Set some extra stuff.
        """
        if self.is_animated:
            self._round_duration()
        
        self.file_extension = get_filename_extension(self.transformed_filename)

        self._populate_base_save_options()

    @cached_property
    def valid_extensions(self):
        return Image.registered_extensions()

    @property
    def is_animated(self):
        return getattr(self.img, "is_animated", False)

    @property
    def has_exif_metadata(self) -> bool:
        return bool(self.img.info.get('exif'))

    @property
    def should_freeze_frame(self):
        """
        Applies to all animated images (gif, apng)
        """
        return self.config.anim is False and self.is_animated

    def _round_duration(self):
        """
        Round the duration of an animation.
        Float values in some apngs cause an error while saving to webp.

        More info: https://github.com/python-pillow/Pillow/issues/7015
        """
        if info := self.img.info.get('duration'):
            self.img.info['duration'] = round(info)

    def get_save_format(self):
        """
        This is used if we are saving image to a buffer.
        Pillow by default interprets the output format from the file extension.
        If there is no file extension, it checks the `format` kwarg.

        Use the file extension to lookup the format in Pillows registered extensions
        mapping:

        ex. extension ".webp" maps to "WEBP" format.
        """
        assert self.file_extension in self.valid_extensions, "Not a valid image extension"

        return self.valid_extensions[self.file_extension]

    def transform(self) -> None:
        """
        Apply all transformation steps to the image.

        1. If animated, check anim to determine whether to freeze first frame
        2. resizing (fit options + trim)
        3. filters (blur, brightness, contrast, sharpen) + rotate
        """

        if self.should_freeze_frame:
            self.freeze_animated_image()
        else:
            self.apply_resize()
            self.apply_effects()

    def process_polish_image(self, original_img_size):
        """
        Do the thing for polished images!
        """
        self.strip_exif_metadata()

        buffer = self.save_to_buffer()



        if self.file_extension == '.webp':
            # self.save_options['lossless'] = True
            # self.strip_exif_metadata()
            # buffer = self.save_to_buffer()
            if buffer.tell() < original_img_size:
                return buffer
            # TODO: return original image here!
        else:
            if not self.has_exif_metadata:
                return self.img

            self.strip_exif_metadata()
            return self.save_to_buffer()

    def process_transform_image(self) -> io.BytesIO:
        """
        Do the thing for transformed images!
        """
        self.transform()

        self.save_options['quality'] = self.config.quality

        if self.config.metadata is False:
            self.strip_exif_metadata()
        else:
            save_options['exif'] = self.img.getexif()

        return self.save_to_buffer()
    
    def _populate_base_save_options(self):
        self.save_options = {
            'format': self.get_save_format(),
            'optimize': True  # has no effect on webp formats
        }

        if self.is_animated:
            self.save_options['save_all'] = True

    @staticmethod
    def save_buffer_to_file(filename, buffer):
        with open(filename, 'wb') as output_file:
            output_file.write(buffer.getbuffer())

    def save_to_buffer(self) -> io.BytesIO:
        buffer = io.BytesIO()

        self.img.save(buffer, **self.save_options)

        buffer.seek(0)
        return buffer

    def apply_resize(self):
        """
        Fit options + trim
        """
        if fit_option := self.config.fit:
            fit_func = getattr(self, self.config.fit.value)

            width, height = self._get_dimensions(
                width=self.config.prepared_width,
                height=self.config.prepared_height
            )

            if fit_option in [FitEnum.SCALE_DOWN, FitEnum.CONTAIN]:
                fit_func(width=width, height=height)
            
            if fit_option in [FitEnum.COVER, FitEnum.CROP]:
                fit_func(width=width, height=height, gravity=self.config.gravity)
            
            if fit_option is FitEnum.PAD:
                fit_func(width=width, height=height, color=self.config.background)

        if self.config.trim:
            self.trim()

    def apply_effects(self):
        """
        filters (blur, brightness, contrast, sharpen) + rotate
        """
        if self.config.background:
            self.fill_background_color()

        for effect in ['blur', 'brightness', 'contrast', 'sharpen', 'rotate']:
            if getattr(self.config, effect, None):
                effect_func = getattr(self, effect)
                effect_func()

    def _get_dimensions(self, width: int = None, height: int = None) -> tuple:
        """
        Calculate new dimensions based on the original image's aspect ratio and a width or height.
        """
        if not width and not height:
            return self.img.size

        if width and height:
            return (width, height)
        
        orig_width, orig_height = self.img.size

        # calculate new height
        if width and not height:
            height = round_up((orig_height / orig_width) * width)
            return (width, height)
        
        # calculate new width
        if not width and height:
            width = round_up((orig_width / orig_height) * height)
            return (width, height)

    def scale_down(self, width: int, height: int) -> None:
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
        self.img.thumbnail((width, height))
    
    def contain(self, width: int, height: int) -> None:
        """
        Image will be resized (shrunk or enlarged) to be as large as possible within the given
        width or height while preserving the aspect ratio.

        Scenarios:
            - all smaller dimensions -> scaled down image
            - all larger dimensions -> scaled up image
            - smaller + larger dimension -> scaled down image according to smaller dimension

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.contain
        """
        self.img = ImageOps.contain(self.img, (width, height))

    def cover(self, width: int, height: int, gravity: GravityEnum = GravityEnum.CENTER) -> None:
        """
        Resizes (shrinks or enlarges) to fill the entire area of width and height. If the image has an aspect ratio
        different from the ratio of width and height, it will be cropped to fit.

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.fit
        """
        # Get Pillow centering position from gravity
        centering = self._get_centering_from_gravity(width=width, height=height, gravity=gravity)

        self.img = ImageOps.fit(self.img, (width, height), centering=gravity)

    def crop(self, width: int, height: int, gravity: GravityEnum = GravityEnum.CENTER) -> None:
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
        centering = self._get_centering_from_gravity(width=width, height=height, gravity=gravity)

        self.img = ImageOps.fit(self.img, (width, height), centering=centering)

    def pad(self, width: int, height: int, color: Optional[Union[str, tuple]] = (0, 0, 0)) -> Image:
        """
        Takes in background color!

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.pad
        """

        if isinstance(color, str) and is_valid_hex(color):
            color = get_rgb_from_hex(color)

        self.img = ImageOps.pad(self.img, (width, height), color=color)

    def trim(self) -> None:
        """
        Cut off pixels from an image.
        TODO: Perform validation to make sure we're pixels don't exceed image dimensions.
        """
        width, height = self.img.size
        trim = self.config.trim

        self.img = self.img.crop(box=(trim.left, trim.top, width-trim.right, height-trim.bottom))
    
    def _get_centering_from_gravity(self, width: int, height: int, gravity: GravityEnum) -> tuple:
        """
        Return the Pillow centering tuple based on gravity option
        and aspect ratio of new image.
        """
        orig_aspect_ratio = self._get_aspect_ratio_factor(width=img.size[0], height=img.size[1])
        new_aspect_ratio = self._get_aspect_ratio_factor(width=width, height=height)

        if gravity is Gravity.CENTER:
            return CENTER_CROP

        if new_aspect_ratio > orig_aspect_ratio:
            return WIDE_IMAGE_GRAVITY_OPTIONS[gravity]
        else:
            return TALL_IMAGE_GRAVITY_OPTIONS[gravity]

    @staticmethod
    def _get_aspect_ratio_factor(width: int, height: int) -> float:
        """
        Calculate aspect ratio factor of an image.
        """
        return round(width / height, 1)

    def blur(self) -> None:
        """
        Applies Gaussian blur to image.

        Looks like blur_radius has no fixed limit according to Pillow docs,
        (ex. blur radius 300 is blurrier than blur radius 250)
        so we can just cap it at 250, similar to CloudFlare.

        CloudFlare range: 1 - 250 inclusive. Anything below 1 is ignored.

        Pillow < 1 values do blur.

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageFilter.html#PIL.ImageFilter.GaussianBlur
        """
        self.img = self.img.filter(ImageFilter.GaussianBlur(self.config.blur))

    def brightness(self) -> None:
        """
        Applies brightness to image.

        Amount of 0 gives you a black image
        Amount of 1.0 gives you original image
        No cap.

        CloudFlare range: 0 - 255 inclusive.

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Brightness
        """
        # Reset brightness if its 0 to avoid black image.
        brighten_amount = 1 if self.config.brightness == 0 else self.config.brightness
        filter = ImageEnhance.Brightness(self.img)

        self.img = filter.enhance(brighten_amount)
    
    def contrast(self) -> None:
        """
        Applies contrast to image.

        Amount of 0 gives you a greyed out image.
        Amount of 1.0 gives you original image
        No cap.

        CloudFlare range: 0 - 255 inclusive.

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageEnhance.html#PIL.ImageEnhance.Contrast
        """
        # Reset contrast if its 0 to avoid 
        contrast_amount = 1 if self.config.contrast == 0 else self.config.contrast
        filter = ImageEnhance.Contrast(self.img)
        
        self.img = filter.enhance(contrast_amount)

    def sharpen(self) -> None:
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
        filter = ImageEnhance.Sharpness(self.img)

        self.img = filter.enhance(self.config.sharpen)

    def rotate(self) -> None:
        """
        Return a rotated version of the image.
        Valid rotation degrees are 90, 180, or 270.

        docs: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.rotate
        """
        self.img = self.img.rotate(angle=self.config.rotate, expand=True)

    def freeze_animated_image(self) -> None:
        """
        Freeze the first frame of an animated image
        """
        # if self.is_animated:
        self.img.seek(0)

    def strip_exif_metadata(self) -> None:
        """
        Removes image EXIF metadata if it exists.
        """
        if 'exif' in self.img.info:
            del self.img.info['exif']

    def fill_background_color(self) -> None:
        """
        Fill transparent images with a background color.
        """
        if self.img.mode in ("RGBA", "LA"):
            background = Image.new(
                self.img.mode[:-1],
                self.img.size,
                self.config.background.as_rgb_tuple()
            )
            background.paste(self.img, mask=self.img)
            self.img = background


"""
i = ImageOptions(width=500)
it = ImageTransformer(config=i, img=Image.open('img/woman_with_phone_and_laptop_EF0nQi5.webp'), transformed_filename='woman_with_phone.png')
it.transform()
buffer = it.save()

# Read in Image
foo = Image.open(buffer)
foo.show()
"""
