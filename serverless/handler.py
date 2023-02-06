import io
import json
import logging
import os

import boto3
from PIL import Image

logger = logging.getLogger(__name__)

s3 = boto3.client('s3')
bucket_name = os.getenv('ORIGINAL_IMG_BUCKET_NAME')
resized_image_bucket_name = os.getenv('RESIZED_IMG_BUCKET_NAME')
img_name = 'coffee.jpg'


def read_img() -> Image:
    file_byte_string = s3.get_object(Bucket=bucket_name, Key=img_name)['Body'].read()
    img = Image.open(io.BytesIO(file_byte_string))
    print(img.format, img.size, img.mode)
    return img


def resize(img: Image) -> None:
    width, height = (img.width // 2, img.height // 2)
    img.thumbnail((width, height))
    name, extension = img_name.rsplit('.', 1)
    filename = f'{name}-thumbnail.{extension}'
    print(filename)
    img.filename = filename


def write_img(img: Image):
    buffer = io.BytesIO()
    img.save(buffer, format=img.format)
    buffer.seek(0)  # rewind pointer back to start
    s3.put_object(Bucket=resized_image_bucket_name, Key=img.filename, Body=buffer)


def hello(event, context):
    body = {
        "message": "Resized image successfully!",
        "input": event,
    }
    status_code = 200
    
    try:
        our_image = read_img()
        resize(our_image)
        write_img(our_image)
        return {"statusCode": status_code, "body": body}
    except Exception as e:
        logger.exception('Error resizing image!')
