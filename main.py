from collections import OrderedDict
from glob import glob
from pathlib import Path
from typing import Union, Optional
from urllib.parse import parse_qs, urlencode, urlparse

from fastapi import Depends, FastAPI, Request, Body, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from PIL import Image
from pydantic import BaseModel, Field, FilePath


from config import ImageOptions, ImageTransformer



VALID_PARAMS = list(ImageOptions.__fields__.keys())
LOCAL_ORIGINAL_IMG_DIRECTORY = 'img2'
LOCAL_TRANSFORMED_IMG_DIRECTORY = 'transformed'
IMAGE_URL_MAPPING = {
    f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/young_family_eating_breakfast.jpg': 'https://m.foolcdn.com/media/affiliates/original_images/young_family_eating_breakfast.jpg',
    f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/women_shopping_in_clothing_store.jpg': 'https://m.foolcdn.com/media/affiliates/original_images/women_shopping_in_clothing_store.jpg',
    f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/woman_with_phone_and_laptop_EF0nQi5.jpg': 'https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg',
    f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/ascent-whiteloader.png': 'https://g.foolcdn.com/static/affiliates/project/images/gifs/ascent-whiteloader.png',
    f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/ascent-whiteloader.gif': 'https://g.foolcdn.com/static/affiliates/project/images/gifs/ascent-whiteloader.gif',
    f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/two_people_with_realtor_in_house_EOhMdBw.jpg': 'https://m.foolcdn.com/media/affiliates/original_images/two_people_with_realtor_in_house_EOhMdBw.jpg',
    # f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/building-a-retirement-income-stream-cover-ipad.png': 'https://g.foolcdn.com/misc-assets/building-a-retirement-income-stream-cover-ipad.png',
}


app = FastAPI()
# app.mount("/static", StaticFiles(directory="img"), name='static')

def str2bool(value) -> bool:
    """
    Replacement for `distutils.strtobool` due to
    its deprecation in Python 3.10.
    """
    true_values = ['true', 't', 'yes', 'y', '1']
    false_values = ['false', 'f', 'no', 'n', '0']
    value = value.lower()
    
    if value in true_values:
        return True
    if value in false_values:
        return False


def get_query_param_dict(querystring: str) -> dict:
    """
    Convert a query param string into a dictionary.
    """
    return {k: v[0] for k, v in parse_qs(querystring.lower()).items()}


def normalize_query_params(query_params: dict) -> OrderedDict:
    """
    Sort and normalize query parameters into an OrderedDict.
    """
    cleaned_params = {k: v for k, v in query_params.items() if k in VALID_PARAMS}

    return OrderedDict(sorted(cleaned_params.items(), key=lambda x: x[0]))


def get_transform_options_str(normalized_query_params: OrderedDict) -> str:
    """
    Flatten query params OrderedDict into string, ex. `height_500_width_500`.
    """
    return '_'.join((f'{k}_{v}' for k, v in normalized_query_params.items()))


def get_transformed_image_name(image_filename: str, transformed_options: str, extension: str = None) -> str:
    """
    Concatenate image name with normalized query parameters
    to create transformed image filename.

    Ex. "coffee.jpg", "height_1000_width_500" -> "coffee_height_1000_width_500.webp"
    """
    if transformed_options:
        return f'{Path(image_filename).stem}_{transformed_options}{extension}'

    return f'{Path(image_filename).stem}{extension}'


def get_extension(accept_header: str, image_filename: str, enable_webp: bool = True) -> str:
    """
    Returns the extension to use for transformed image.
    """
    if accept_header and 'image/webp' in accept_header and enable_webp:
            return '.webp'
    return Path(image_filename).suffix


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/raw/{img_name:path}")
def serve_original_local_image(img_name: str):
    if not Path(img_name).exists():
        return JSONResponse(status_code=404, content={"error": "Image not found!"})
    
    return FileResponse(img_name)


@app.get("/transform/{img_name:path}")
def transform_and_serve_image(img_name: str, request: Request, options: ImageOptions = Depends(ImageOptions)):

    if not Path(img_name).exists():
        return JSONResponse(status_code=404, content={"error": "Image not found!"})

    print(f'{img_name = }')
    print(f'{request.query_params = }')
    print(f'{request.headers = }')
    print(f"{request.headers['accept'] = }")

    all_params: dict = get_query_param_dict(str(request.query_params))
    normalized_query_params: OrderedDict = normalize_query_params(all_params)
    transform_options_str: str = get_transform_options_str(normalized_query_params)
    
    print(f'{all_params = }')
    print(f'{normalized_query_params = }')
    print(f'{transform_options_str = }')

    # if valid query params were passed, proceed to process image options
    print(options)

    extension = get_extension(
        accept_header=request.headers.get('accept'),
        image_filename=img_name,
        enable_webp=str2bool(all_params.get('enable_webp', 'true'))
    )

    transformed_img_name = get_transformed_image_name(
        image_filename=img_name,
        transformed_options=transform_options_str,
        extension=extension
    )
    output_file = f'{LOCAL_TRANSFORMED_IMG_DIRECTORY}/{transformed_img_name}'
    print('🤞', output_file)

    if not Path(output_file).exists():
        img = Image.open(img_name)
        transformer = ImageTransformer(config=options, img=img, transformed_filename=output_file)
        # transformer.transform()
        # transformer.save_to_file()
        buffer = transformer.process_transform_image()
        transformer.save_buffer_to_file(filename=output_file, buffer=buffer)
        print('✅', transformed_img_name)
    else:
        print('🌟 output file exists!', output_file)
    return FileResponse(output_file)


@app.get('/compare/{img_name:path}')
def compare_images(img_name: str, request: Request):
    
    print('query params', request.query_params)
    # return RedirectResponse(url=f'/transform/{img_name}')
    
    if mapped_img := IMAGE_URL_MAPPING.get(img_name):
        return {
            "transformed image url": f"/transform/{img_name}?{str(request.query_params)}",
            "CloudFlare image url": f"{mapped_img}?{str(request.query_params)}"
        }
    else:
        return JSONResponse(status_code=404, content={"error": "Image not in mapping!"})
