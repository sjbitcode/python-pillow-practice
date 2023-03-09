from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from PIL import Image
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
    NonNegativeFloat
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
        "1,2,3,4"          TrimPixels(top=1, right=2, bottom=3, left=4)
        "1.1, 2.5, 3, 4"   TrimPixels(top=1, right=2, bottom=3, left=4)
        """
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

    @staticmethod
    def round_up(value):
        rounded = Decimal(value).quantize(1, rounding=ROUND_HALF_UP)
        return int(rounded)


# i = ImageOptions(anim='true', background='black', blur=20, rotate=180, w=90, trim='1.5,2,3,4')
i = ImageOptions(w=90, dpr=2)

# import pdb; pdb.set_trace()

@dataclass
class ImageTransformer:
    config: ImageOptions
    img: Image

    def adjust_options(self):
        cfg = self.config

        # ensure `width` or `height` exists for certain options
        if not (cfg.width or cfg.height):

            if cfg.dpr:
                cfg.dpr = None

            if cfg.fit:
                cfg.fit = None

        # multiply height and width by dpr
        if cfg.dpr:
            for attr in ['width', 'height', 'w', 'h']:
                orig_dimension = getattr(cfg, attr)
                setattr(cfg, attr, orig_dimension*cfg.dpr)

    def transform(self):
        """
        Apply all transformation steps to the image.

        1. Multiply width and height by dpr?
        2. If animated and has transform options, save first frame and do transformations on frame
        3. resizing (fit options + trim)
        4. filters (blur, brightness, contrast, sharpen) + rotate
        """
        cfg = self.config
        orig_size = self.img.size  # TODO: do we need this?
        
        # Are we working with animated image? If so, check if anim is True

    def save(self):
        pass