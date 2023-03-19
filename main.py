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


def normalize_querystring_params(querystring: str) -> str:
    """
    Sort and normalize query parameters into a string.

    Ex. "width=500&height=1000" -> "height_1000_width_500"
    """
    valid_params = ImageOptions.__fields__.keys()
    params_dict = {k: v[0] for k, v in parse_qs(querystring.lower()).items()}
    cleaned_params = {k: v for k, v in params_dict.items() if k in valid_params}
    sorted_params = OrderedDict(sorted(cleaned_params.items(), key=lambda x: x[0]))

    return '_'.join((f'{k}_{v}' for k, v in sorted_params.items()))


def get_transformed_image_name(image_filename: str, normalized_qs: str, extension: str = None) -> str:
    """
    Concatenate image name with normalized query parameters
    to create transformed image filename.

    Ex. "coffee.jpg", "height_1000_width_500" -> "coffee_height_1000_width_500.webp"
    """
    if normalized_qs:
        return f'{Path(image_filename).stem}_{normalized_qs}{extension}'

    return f'{Path(image_filename).stem}{extension}'


def get_extension(accept_header: str, image_filename: str) -> str:
    """
    Returns the extension to use for transformed image.
    """
    if accept_header and 'image/webp' in accept_header:
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

    print('img_name', img_name)
    print('query params', request.query_params)
    print('query params', type(request.query_params))
    print(request.headers)
    print(request.headers['accept'])
    print(str(request.query_params))

    normalized_qs = normalize_querystring_params(str(request.query_params))
    print('normalized qs', normalized_qs)

    # if valid query params were passed, proceed to proceed image options
    # if normalized_qs:
    print(options)

    extension = get_extension(
        accept_header=request.headers.get('accept'),
        image_filename=img_name
    )

    transformed_img_name = get_transformed_image_name(
        image_filename=img_name,
        normalized_qs=normalized_qs,
        extension=extension
    )
    output_file = f'{LOCAL_TRANSFORMED_IMG_DIRECTORY}/{transformed_img_name}'
    print('🤞', output_file)

    if not Path(output_file).exists():
        img = Image.open(img_name)
        transformer = ImageTransformer(config=options, img=img, transformed_filename=output_file)
        transformer.transform()
        transformer.save_to_file()
        print('✅', transformed_img_name)
    else:
        print('🌟 output file exists!', output_file)
    return FileResponse(output_file)
    # else:
    #     return FileResponse(img_name)


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
