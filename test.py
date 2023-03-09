from main import *

"""
- https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg
- https://m.foolcdn.com/media/affiliates/original_images/young_family_eating_breakfast.jpg
- https://m.foolcdn.com/media/affiliates/original_images/women_shopping_in_clothing_store.jpg

Trim literally cuts x pixels off of the specified sides of the image,
regardless of how big that image is, and then passes it to the resize/crop option
"""

#######################################
# SCALE DOWN
# Shrink image preserving aspect ratio. Image is never enlarged.
#######################################

"""
This tests that `scale_down` given one smaller dimension scales down the image.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
new_width, new_height = get_new_dimensions(img, width=500)
scale_down_width500 = scale_down(img, width=new_width, height=new_height)
scale_down_width500.save('transformed2/woman_with_phone_and_laptop__scale_down_width500.jpg')

"""
This tests that `scale_down` given one larger dimension returns original image.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?height=3000
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
new_width, new_height = get_new_dimensions(img, height=3000)
scale_down_height3000 = scale_down(img, width=new_width, height=new_height)
scale_down_height3000.save('transformed2/woman_with_phone_and_laptop__scale_down_height3000.jpg')

"""
This tests that `scale_down` given one smaller and one larger dimension returns original image.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?height=3000&width=500
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
scale_down_width500_height3000 = scale_down(img, width=500, height=3000)
scale_down_width500_height3000.save('transformed2/woman_with_phone_and_laptop__scale_down_width500_height3000.jpg')

"""
The following tests that `scale_down` given two smaller dimensions scales down the image while preserving aspect ratio.

CloudFlare example:
    1. https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&height=300
    2. https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=300&height=500
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
scale_down_width500_height300 = scale_down(img, width=500, height=300)
scale_down_width500_height300.save('transformed2/woman_with_phone_and_laptop__scale_down_width500_height300.jpg')

img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
scale_down_width300_height500 = scale_down(img, width=300, height=500)
scale_down_width300_height500.save('transformed2/woman_with_phone_and_laptop__scale_down_width300_height500.jpg')

"""
This tests that `scale_down` given two larger dimensions returns original image.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=3000&height=2000
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
scale_down_width3000_height2000 = scale_down(img, width=3000, height=2000)
scale_down_width3000_height2000.save('transformed2/woman_with_phone_and_laptop__scale_down_width3000_height2000.jpg')


#######################################
# CONTAIN
# Resize (shrink or enlarge while preserving aspect ratio)
#######################################

"""
This tests that `contain` given one smaller dimension scales down the image.
Same as `scale_down`.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&fit=contain
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
new_width, new_height = get_new_dimensions(img, width=500)
contain_width500 = contain(img, width=new_width, height=new_height)
contain_width500.save('transformed2/woman_with_phone_and_laptop__contain_width500.jpg')


"""
This tests that `contain` given one larger dimension enlarges image while preserving aspect ratio.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?height=2000&fit=contain
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
new_width, new_height = get_new_dimensions(img, height=2000)
contain_height2000 = contain(img, width=new_width, height=new_height)
contain_height2000.save('transformed2/woman_with_phone_and_laptop__contain_height2000.jpg')


"""
This tests that `contain` given one smaller and one larger dimension returns original image.
Same as `scale_down`.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&height=3000&fit=contain
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
contain_width500_height3000 = contain(img, width=500, height=3000)
contain_width500_height3000.save('transformed2/woman_with_phone_and_laptop__contain_width500_height3000.jpg')


"""
The following tests that `contain` given two smaller dimensions scales down the image while preserving aspect ratio.
Same as `scale_down`.

CloudFlare example:
    1. https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&height=300&fit=contain
    2. https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=300&height=500&fit=contain
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
contain_width500_height300 = contain(img, width=500, height=300)
contain_width500_height300.save('transformed2/woman_with_phone_and_laptop__contain_width500_height300.jpg')

img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
contain_width300_height500 = contain(img, width=300, height=500)
contain_width300_height500.save('transformed2/woman_with_phone_and_laptop__contain_width300_height500.jpg')


"""
This tests that `contain` given two larger dimensions enlarges image while preserving aspect ratio.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=3000&height=2000&fit=contain
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
contain_width3000_height2000 = contain(img, width=3000, height=2000)
contain_width3000_height2000.save('transformed2/woman_with_phone_and_laptop__contain_width3000_height2000.jpg')


#######################################
# COVER
# Resize (shrink or enlarge) to fix exact dimensions. Will crop to fit if new dimensions don't match aspect ratio.
#######################################

"""
This tests that `cover` given one smaller dimension scales down the image.
Same as `scale_down` and `contain`.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&fit=cover (same as `scale_down` and `contain`).
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
new_width, new_height = get_new_dimensions(img, width=500)
cover_width500 = cover(img, width=new_width, height=new_height)
cover_width500.save('transformed2/woman_with_phone_and_laptop__cover_width500.jpg')


"""
This tests that `cover` given one larger dimension enlarges image while preserving aspect ratio.
Same as `contain`.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?height=2000&fit=cover
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
new_width, new_height = get_new_dimensions(img, height=2000)
cover_height2000 = cover(img, width=new_width, height=new_height)
cover_height2000.save('transformed2/woman_with_phone_and_laptop__cover_height2000.jpg')


"""
This tests that `cover` given one smaller and one larger dimension returns will crop to fit image within new dimensions.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&height=3000&fit=cover
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
cover_width500_height3000 = cover(img, width=500, height=3000)
cover_width500_height3000.save('transformed2/woman_with_phone_and_laptop__cover_width500_height3000.jpg')


"""
This tests that `cover` given all smaller dimensions will shrink and crop to fit image with new dimensions.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=500&height=300&fit=cover
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
cover_width500_height300 = cover(img, width=500, height=300)
cover_width500_height300.save('transformed2/woman_with_phone_and_laptop__cover_width500_height300.jpg')


"""
This tests that `cover` given all larger dimensions will enlarge image and crop to fit image with new dimensions.

CloudFlare example: https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=3000&height=2000&fit=cover
"""
img = Image.open('img2/woman_with_phone_and_laptop_EF0nQi5.jpg')
cover_width3000_height2000 = cover(img, width=3000, height=2000)
cover_width3000_height2000.save('transformed2/woman_with_phone_and_laptop__cover_width3000_height2000.jpg')
