from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from PIL import Image, ImageColor, ImageOps, ImageFilter, ImageEnhance
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


class TrimPixels(BaseModel):  # round floats?
    top: NonNegativeInt
    right: NonNegativeInt
    bottom: NonNegativeInt
    left: NonNegativeInt

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
    quality: conint(ge=0, le=100) = Field(default=75)  # has some PNG caveat with PNG8 color palette  # should we stick with 85 - CloudFlare's defaults?
    rotate: Optional[conint(multiple_of=90)]
    sharpen: Optional[confloat(ge=0, le=10)]
    trim: Optional[TrimPixels]

    @validator('trim', pre=True)
    def save_trim_to_model(cls, values):
        """
        Convert list of strings into a `TrimPixels` instance.

        Example:
            - "1,2,3,4"          TrimPixels(top=1, right=2, bottom=3, left=4)
            - "1.1, 2.5, 3, 4"   TrimPixels(top=1, right=2, bottom=3, left=4)
        """
        if isinstance(values, TrimPixels):
            return values

        try:
            pixels: list = values.replace(' ', '').split(',')
            trim_values = [cls.round_up(float(x)) for x in pixels if x]
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
        width = cls.round_up(width) if width else None
        values["w"] = values["width"] = width

        height = values.get("height") or values.get("h")
        height = cls.round_up(height) if height else None
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

    @property
    def is_animated(self):
        return getattr(self.img, "is_animated", False)
    
    @property
    def should_freeze_frame(self):
        return self.config.anim is False and self.is_animated

    def transform(self) -> None:
        """
        Apply all transformation steps to the image.

        2. If animated, check anim to determine whether to freeze first frame
        3. resizing (fit options + trim)
        4. filters (blur, brightness, contrast, sharpen) + rotate
        """

        # TODO: don't apply transformations on animated images
        if self.should_freeze_frame:
            pass

        # resizing
        self.apply_resize()

        # filters + rotate
        self.apply_effects()

    def save(self):
        pass

    def apply_resize(self):
        """
        Fit options + trim
        """
        if self.config.prepared_height or self.config.prepared_width:
            width, height = self.get_dimensions()
        
        # TODO: call all fit + trim methods here

    def apply_effects(self):
        """
        filters (blur, brightness, contrast, sharpen) + rotate
        """
        # TODO: call all filter + rotate methods here
        pass

    def get_dimensions(self, width: int = None, height: int = None) -> tuple:
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

    def cover(self, width: int, height: int, gravity: tuple = CENTER_CROP) -> Image:
        """
        Resizes (shrinks or enlarges) to fill the entire area of width and height. If the image has an aspect ratio
        different from the ratio of width and height, it will be cropped to fit.

        docs: https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#PIL.ImageOps.fit
        """
        self.img = ImageOps.fit(self.img, (width, height), centering=gravity)

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

        self.img = ImageOps.fit(img, (width, height), centering=centering)