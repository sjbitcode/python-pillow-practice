# ICC Profile in Pillow

Some images have an attribute called `icc_profile`, for example:
```python
>>> img.info.keys()
dict_keys(['jfif', 'jfif_version', 'dpi', 'jfif_unit', 'jfif_density', 'exif', 'photoshop', 'icc_profile'])
>>>
>>> img.info['icc_profile'][:20]
b'\x00\x00\x020ADBE\x02\x10\x00\x00mntrRGB '
```

In short, [ICC profiles](https://www.graphicsmill.com/docs/gm/working-with-embedded-icc-profiles.htm#:~:text=In%20color%20management%2C%20an%20ICC,correctly%20color%20match%20the%20file.) are color characteristics that can be embedded into an image to make sure an application displays it correctly.

## Usage in Pillow
When saving images, be sure to include the `icc_profile` in the save options if it exists in the image's `info` dict.

Not saving it can cause the output image to look different than the original!

This applies to whether you're saving JPEG, PNG, TIFF, WEBP. [GIFs in general have ICC profiles](http://justsolve.archiveteam.org/wiki/ICC_profile#:~:text=In%20a%20GIF%20file%2C%20an,uses%20application%20identifier%20%22ICCRGBG1012%22.), but Pillow doesn't seem to document `icc_profile` as a [save option for gifs](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif-saving).

```python
from PIL import Image

img = Image.open('img/young_family_eating_breakfast.jpg')

print('icc_profile' in img.info.keys())

img.save('transformed/young_family_eating_breakfast.webp', icc_profile=img.info['icc_profile'])
```

