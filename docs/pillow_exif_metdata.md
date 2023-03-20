# Exif metadata in Pillow

Pillow does not save EXIF metadata on JPEG, PNG, WEBP, TIFF images. [GIFs don't use EXIF metadata](https://superuser.com/questions/556315/gif-image-exif-tags).

See these Pillow [issue](https://github.com/python-pillow/Pillow/issues/6804) and [PR](https://github.com/python-pillow/Pillow/pull/6819) for more info

```python
from PIL import Image

img = Image.open('img/puppy.jpg')
print(img.info.get('exif'))

# Store EXIF data
exif = img.getexif()  # Exif object, may or may not be empty
print(list(exif.keys()))
exif[0x9286] = 'test'
print(list(exif.keys()))

# Save image
img.info['exif'] = exif.tobytes()
img.save('transformed/puppy_exif_test.jpg')

# Open up the saved image and check that exif data is not there!
puppy_exif_test = Image.open('transformed/puppy_exif_test.jpg')
print(puppy_exif_test.info.keys())
assert 'exif' not in puppy_exif_test.info.keys()
```