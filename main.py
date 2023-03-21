import io
from collections import OrderedDict
from glob import glob
import json
from pathlib import Path
from typing import Union, Optional
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from fastapi import Depends, FastAPI, Request, Body, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from PIL import Image
from pydantic import BaseModel, Field, FilePath, HttpUrl, root_validator


from config import ImageOptions, ImageTransformer


IMAGE_URL_MAPPING = {}
IMAGE_URL_MAPPING_FILE = 'image_mapping.json'
VALID_PARAMS = list(ImageOptions.__fields__.keys())
LOCAL_ORIGINAL_IMG_DIRECTORY = 'tmf-original'
LOCAL_TRANSFORMED_IMG_DIRECTORY = 'tmf-transformed'


def populate_image_mapping() -> None:
    """
    Load json file to image mapping dict.
    """
    with open(IMAGE_URL_MAPPING_FILE) as f:
        global IMAGE_URL_MAPPING
        IMAGE_URL_MAPPING = json.load(f)


def save_image_to_mapping(local_file_path: str, image_url: str) -> None:
    """
    Save image to mapping by updating mapping dict and updating json file.
    """
    IMAGE_URL_MAPPING[local_file_path] = image_url

    with open(IMAGE_URL_MAPPING_FILE, 'w') as f:
        json.dump(IMAGE_URL_MAPPING, f, indent=4)


def configure():
    populate_image_mapping()


app = FastAPI()
configure()
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
    query_param_sentence = "You can pass in transform query parameters at this endpoint."

    return {
        "navigation": {
            "view": {
                "endpoint": f"/raw/img/puppy.jpg",
                "description": "View a local image"
            },
            "transform" :{
                "endpoint": f"/transform/img/puppy.jpg?width=500",
                "description": f"Transform a local image. {query_param_sentence}"
            },
            "compare all": {
                "endpoint": '/compare',
                "description": f"View all pairs of local images and CloudFlare versions. {query_param_sentence}"
            },
            "compare single": {
                "endpoint": '/compare/tmf-original/young_family_eating_breakfast.jpg',
                "description": f"View a local image and it's CloudFlare version. {query_param_sentence}"
            },
            "download": {
                "endpoint": '/download/https://m.foolcdn.com/media/affiliates/original_images/young_family_eating_breakfast.jpg',
                "description": "Download a foolcdn image and save to image mapping"
            }
        }
    }


@app.get("/download/{image_url:path}")
async def download_image(image_url: HttpUrl):
    allowed_hosts = ['g.foolcdn.com', 'm.foolcdn.com', 'staging.m.foolcdn.com', 'staging.g.foolcdn.com']

    if image_url.host not in allowed_hosts:
        return JSONResponse(status_code=400, content={"error": f"Image url must be one of the valid foolcdn domains, {allowed_hosts}"})

    async with httpx.AsyncClient() as client:
        url = f'{image_url.scheme}://{image_url.host}{image_url.path}'
        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'}
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()

    # Save image
    filename = f'{LOCAL_ORIGINAL_IMG_DIRECTORY}/{Path(image_url.path).name}'
    buffer = io.BytesIO(resp.content)
    ImageTransformer.save_buffer_to_file(filename=filename, buffer=buffer)

    # Store in mapping
    save_image_to_mapping(local_file_path=filename, image_url=url)

    return RedirectResponse(url=f'/transform/{filename}')


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
    print(f'🤞 {output_file = }')

    if not Path(output_file).exists():
        img = Image.open(img_name)
        transformer = ImageTransformer(config=options, img=img, transformed_filename=output_file)
        buffer = transformer.process_transform_image()
        transformer.save_buffer_to_file(filename=output_file, buffer=buffer)
        print('✅', transformed_img_name)
    else:
        print('🌟 output file exists!', output_file)
    return FileResponse(output_file)


@app.get('/compare')
def view_all_comparison_images(request: Request):
    response = []

    for img_name, mapped_img in IMAGE_URL_MAPPING.items():

        transform_img_url = f"/transform/{img_name}?{str(request.query_params)}" if request.query_params else f"/transform/{img_name}"
        cloudflare_img_url = f"{mapped_img}?{str(request.query_params)}" if request.query_params else mapped_img

        entry = {
            "TMF Transformed image url": transform_img_url,
            "CloudFlare image url": cloudflare_img_url,
            "compare url": f"/compare/{img_name}"
        }

        response.append(entry)

    return response


@app.get('/compare/{img_name:path}')
def compare_images(img_name: str, request: Request):

    if not img_name:
        return JSONResponse(status_code=400, content={"error": "Must include an image path!"})

    print('query params', request.query_params)

    if mapped_img := IMAGE_URL_MAPPING.get(img_name):

        transform_img_url = f"/transform/{img_name}?{str(request.query_params)}" if request.query_params else f"/transform/{img_name}"
        cloudflare_img_url = f"{mapped_img}?{str(request.query_params)}" if request.query_params else mapped_img

        return {
            "TMF Transformed image url": transform_img_url,
            "CloudFlare image url": cloudflare_img_url
        }
    else:
        return JSONResponse(status_code=404, content={"error": "Image not in mapping!"})
