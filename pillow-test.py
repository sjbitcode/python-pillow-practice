import io
import os

import boto3
from PIL import Image


os.environ['AWS_PROFILE'] = "aws-test"
s3 = boto3.client('s3', region_name='us-east-1')

# bucket_name = 'sangeeta-original-images'
# resized_image_bucket_name = 'sangeeta-transformed-images'
# img_name = 'coffee.jpg'


# def read_img() -> Image:
#     file_byte_string = s3.get_object(Bucket=bucket_name, Key=img_name)['Body'].read()
#     img = Image.open(io.BytesIO(file_byte_string))
#     print(img.format, img.size, img.mode)
#     return img


# def resize(img: Image) -> None:
#     width, height = (img.width // 2, img.height // 2)
#     img.thumbnail((width, height))
#     name, extension = img_name.rsplit('.', 1)
#     filename = f'{name}-thumbnail.{extension}'
#     print(filename)
#     img.filename = filename


# def write_img(img: Image):
#     buffer = io.BytesIO()
#     img.save(buffer, format=img.format)
#     buffer.seek(0)  # rewind pointer back to start
#     s3.put_object(Bucket=resized_image_bucket_name, Key=img.filename, Body=buffer)


our_image = read_img()
resize(our_image)
write_img(our_image)

img = Image.open("img/coffee.jpg")
print(img.format, img.size, img.mode)

img.thumbnail((img.width // 2, img.height // 2))

buffer = io.BytesIO()
img.save(buffer, format=img.format)
buffer.seek(0)  # rewind pointer back to start

img.filename = f'{img.filename}-resized.jpg'

s3.put_object(Bucket='sangeeta-original-images', Key='resized-image.jpg', Body=buffer)
