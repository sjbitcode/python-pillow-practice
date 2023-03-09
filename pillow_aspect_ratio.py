import math

from PIL import Image


def preserve_aspect_ratio(img, new_width, new_height):

    def round_aspect(number, key):
        return max(min(math.floor(number), math.ceil(number), key=key), 1)

    new_width, new_height = tuple(map(math.floor, (new_width, new_height)))
    width, height = img.size

    if new_width >= width and new_height >= height:
        return

    aspect = width / height
    new_aspect = new_width / new_height

    # too wide, recalculate width
    if new_aspect >= aspect:
        new_width = round_aspect(new_height * aspect, key=lambda n: abs(aspect - n / new_height))

    # too tall, recalculate height
    else:
        new_height = round_aspect(
            new_width / aspect, key=lambda n: 0 if n == 0 else abs(aspect - new_width / n)
        )
    return new_width, new_height


img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')

preserve_aspect_ratio(img, 500, 3000)
