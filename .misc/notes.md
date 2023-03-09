Lambda supports Python 3.7-3.9 ([lambda runtime reference](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html))

Python 3.9 can the latest versions of Pillow, starting from Pillow 8.0 ([Pillow Python support reference](https://pillow.readthedocs.io/en/stable/installation.html#python-support))

👀 https://pillow.readthedocs.io/en/stable/installation.html#continuous-integration-targets


AWS Lambda has a 6 MB invocation payload request and response limit ([reference](https://docs.aws.amazon.com/solutions/latest/serverless-image-handler/considerations.html))

[AWS PIL error and how to fix it](https://derekurizar.medium.com/aws-lambda-python-pil-cannot-import-name-imaging-11b2377d31c4)

## Image notes

### Examples
- fill background color - `https://g.foolcdn.com/static/affiliates/project/images/gifs/ascent-whiteloader.png?background=%23000000`
- fit=pad + background - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?height=1200&width=1200&fit=pad&background=%23000000`
- anim=false - `https://g.foolcdn.com/static/affiliates/project/images/gifs/ascent-whiteloader.gif?anim=false`
  - this works when returned image is webp. When I do the browser header trick to disallow webp/avif, the anim=false has no effect on gif
- blur - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?blur=200`
  - CloudFlare supports blur values between 1 and 250
  - blur value below 1 doesn't have any effect
  - how to handle values that exceed limits? throw an error like `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?blur=300`
  - blur can accept float values - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?blur=254.29381982342948`
- brightness - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?brightness=2.0`
  - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?brightness=10.0`
  - max value is 255, after that CloudFlare throws an error - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=255`
  - no max decimal place - this works: `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=5.901343409340293423949234823`
  - 0 gives original image - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=0`
  - anything from 0.1 to 1 is darkish - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=0.2`
  - so 0 and 1 should give you original image, but 0.1 - 1 should be darker.
  - brightness applied after fit=pad
- contrast - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?contrast=10.0`
  - max value is 255, after that CloudFlare throws an error - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?contrast=255`
- dpr
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?dpr=100&width=500`
  - can't be more than 3, CloudFlare adds a warning header `warning: cf-images 299 "dpr > 3 should never be used"`
  - doesn't make a difference if height and width aren't passed -- `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?dpr=2&height=300` vs `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?dpr=2`
- height and width
  - `https://g.foolcdn.com/image/?url=https%3A%2F%2Fg.foolcdn.com%2Feditorial%2Fimages%2F711554%2Fa-hand-drawing-money-signs-and-an-upward-arrow-on-a-chalkboard.jpg&h=104&w=184`
- fit cover
  - if you pass it dimensions different than aspect ratio, it will crop to fit
    - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=1600&height=2400&fit=cover`
- Trim
  - https://m.foolcdn.com/media/affiliates/original_images/young_family_eating_breakfast.jpg?trim=10,300,1450,2030
- Sharpen
  - https://m.foolcdn.com/media/affiliates/original_images/young_family_eating_breakfast.jpg?sharpen=5.5
    - will throw error if over 10
- Combination
  - if you pass multiple of the same query params, the first one seems to be the one taken
    - the first fit option is used `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=3000&height=2000&fit=crop&fit=cover`
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?blur=250&fit=pad&width=2000&height=2000&background=black`
    - blur comes after (the black background + image is blurred together)
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=0.2&fit=pad&width=2500&height=3000`
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?blur=250&brightness=255&fit=pad&width=2000&height=2000&background=black`
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=10&fit=pad&width=2500&height=3000&background=%23FF3333` (red background)
    - brightness is applied after fit=pad (background gets brighter)
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?contrast=10&fit=pad&width=2500&height=3000&background=%23FF3333`
    - contrast applied after fit=pad (background is not contrasted!)
  - when transform options are applied to gifs, they're applied to the first frame of the gif
    - fit=pad with a background returns as jpg
  - `width` and `height` with `w` and `h`
    - https://m.foolcdn.com/media/affiliates/original_images/hands_typing_on_laptop_1zVshrl_dEN10Pj.jpg?w=500&width=550&h=200&height=300&fit=cover
    - `width` and `height` will take precedence
  - dpr, trim
    - lines up with what Tim said -- trim comes after resizing!!
    - https://m.foolcdn.com/media/affiliates/original_images/young_family_eating_breakfast.jpg?dpr=2&width=3000&fit=cover&trim=10,300,5,10
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?height=200&width=200&fit=cover&trim=0.5,0.5,0.5,0.5`
    - looks like this does fit after everything?



### Color modes
- RGB: RBG is a very common color mode for digital images. It uses 3 channels to represent color Red-Green-Blue.
- RGBA on the other hand is a color mode that can represent “transparency” through its Alpha channel. This type of image can only be saved as PNG or GIF image file formats which support transparency.
- 1 mode: 1 color mode in Python PIL represents 1-bit image. As 1-bit can only take 2 values; 0 and 1, 1-bit images only have white or black colors without any shades of gray.
- 1 channel = 8bits
- L mode: L grayscale image you will get pixels 1-channel which can take any value between 0-255 inclusive.
- LA mode: LA mode is very similar to LA mode except it has an extra channel called Alpha for transparency. This channel can also take 256 values which makes LA color mode 16-bit (8-bit plus 8-bit for alpha channel) or 32-bit (24-bit plus 8-bit for alpha) depth.
- La mode: La grayscale color mode is very similar to LA grayscale color mode. The difference is alpha channel in La mode is predetermined.
- alpha vs premultiplied alpha:
  - alpha (or unassociated or non-premultiplied) preserves both color or luminosity information and additionally stores an alpha channel which allows recovering color data or making new adjustments conveniently later on. This can be called as lossless transparency method.
  - premultiplied alpha on the other hand doesn’t preserve color data and instead contains the end result from blending transparency and colors on pixels hence the name premultiplied alpha. Other alpha is more common and regularly used in general since it’s a safer approach for digital image editing. In most cases you don’t want to not be able to adjust transparency independently later on.

### Sources
- https://holypython.com/python-pil-tutorial/color-modes-explained-for-digital-image-processing-in-python-pil/
- https://note.nkmk.me/en/python-pillow-putalpha/
- background to transparent image
  - https://stackoverflow.com/questions/50739732/how-to-covert-png-to-jpeg-using-pillow-while-image-color-is-black
  - https://stackoverflow.com/questions/5324647/how-to-merge-a-transparent-png-image-with-another-image-using-pil/5324782#5324782
  - https://www.geeksforgeeks.org/how-to-merge-a-transparent-png-image-with-another-image-using-pil/
  - https://stackoverflow.com/questions/38627870/how-to-paste-a-png-image-with-transparency-to-another-image-in-pil-without-white
- gaussian blur
  - https://stackoverflow.com/questions/62968174/for-pil-imagefilter-gaussianblur-how-what-kernel-is-used-and-does-the-radius-par
- https://www.rapidtables.com/web/color/RGB_Color.html
- border
  - https://gist.github.com/namieluss/a440061734075d929f0c6b9f6bd919c7
- DEFAULT BEHAVIOR OF CLOUDFLARE FIT
  - https://community.cloudflare.com/t/image-resizing-default-behavior-of-fit-parameter/442651
- aspect ratio
  - https://opensource.com/life/15/2/resize-images-python
  - https://www.holisticseo.digital/python-seo/resize-image/
  - https://elitescreens.eu/pages/screen-size-calculator
  - https://andrew.hedges.name/experiments/aspect_ratio/
- cropping centering - https://www.pythoninformer.com/python-libraries/pillow/imageops-resizing/
- Exif data
  - https://stackoverflow.com/questions/17042602/preserve-exif-data-of-image-with-pil-when-resizecreate-thumbnail
  - https://exiv2.org/tags.html
  - image with exif metadata - `young_family_eating_breakfast.jpg`
- Compression
  - https://stackoverflow.com/questions/30771652/how-to-perform-jpeg-compression-in-python-without-writing-reading
  - https://jdhao.github.io/2019/07/20/pil_jpeg_image_quality/
- CloudFlare Polish feature
  - https://developers.cloudflare.com/images/polish/compression/ (`Polish will not be applied to URLs using Image Resizing`)
  - https://blog.cloudflare.com/a-very-webp-new-year-from-cloudflare/
  - https://blog.cloudflare.com/introducing-polish-automatic-image-optimizati/
  - https://webmasters.stackexchange.com/questions/136565/can-i-use-cloudflare-to-remove-gps-location-data-from-the-exif-metadata-of-image
  - https://blog.cloudflare.com/a-very-webp-new-year-from-cloudflare/ (GOOD ARTICLE)
- Resize images with CloudFlare either with pre-defined URL or image workers (https://developers.cloudflare.com/images/image-resizing/)
- CloudFlare polished header info
  - https://exabytes.freshdesk.com/en/support/solutions/articles/14000100604-using-cloudflare-polish-to-compress-images#:~:text=The%20cf%2Dpolished%20header%20represents,and%20Polish%20can%20be%20applied.
  - https://support.cloudflare.com/hc/en-us/articles/4412244347917-Troubleshoot-common-Cf-Polished-statuses
  - https://support.cloudflare.com/hc/en-us/articles/4412024022029-Troubleshoot-Image-Resizing-problems
- CloudFlare default cache behavior
  - https://developers.cloudflare.com/cache/about/default-cache-behavior/
- CloudFlare polish/unpolished images
  - https://g.foolcdn.com/misc-assets/fastly.png
  - https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg
  - https://g.foolcdn.com/art/fool15/bg/fool-logo.png
    - https://billboard.fool.com/bigip/us_redirects/?search=foolcdn
    - redirects to https://g.foolcdn.com/art/fool15/bg/fool-logo.png
    - when `Accept` header doesn't have `img/webp` it will serve original (not default to avif because it is not processed by image worker)
    - 

## Thoughts
- cache webp/avif versions?
- warm cache before cutover
- cloudflare worker limits - https://developers.cloudflare.com/workers/platform/limits/
  - https://developers.cloudflare.com/images/image-resizing/format-limitations/#format-limitations
  - not sure why this image doesn't scale greater than dpr=3 - `https://g.foolcdn.com/image/?url=https%3A%2F%2Fg.foolcdn.com%2Feditorial%2Fimages%2F711554%2Fa-hand-drawing-money-signs-and-an-upward-arrow-on-a-chalkboard.jpg&h=104&w=184&dpr=3`
- try to get images with exif data from "transformed image" as original file extension (don't pass Accept header with image/webp)

## Pillow Compression Notes
- https://stackoverflow.com/questions/72245578/remove-exif-from-image-before-upload-to-s3-in-python
- https://thecodersblog.com/compress-image-python
  - `optimize` parameter is supported by the following image formats: JPEG, PNG, WebP, and TIFF.
  - The `quality` parameter is supported by the following image formats: JPEG, WebP, and TIFF.
    - quality (changing png palette with pillow) - https://stackoverflow.com/questions/71733860/how-can-change-24-bit-depth-to-8-bit-depth-in-python-in-pillow
    - https://stackoverflow.com/questions/6114534/converting-png32-to-png8-with-pil-while-preserving-transparency
- webp images can have exif data, so we still need to strip data before saving webp
- png
  - when saving a png as png with `optimize=True`, it reduces file size a little
  - when saving a png as webp with `optimize=True`, it reduces file size considerably
  - `webp` without optimize seems to be the same as with `optimize=True`
  - when saving a png as a png, `quality` does not make a difference, because png images are lossless
- `webp` are lossy, so `quality` does make a difference
- jpg
  - can only use `quality=keep` when original and saved image are jpg, BUT this (with or without `optimize=True`) actually results in a larger image size!
  - when saving as jpg with Pillow's default `quality` value (75), it does reduce image size a little
  - when saving as jpg with Pillow's default `quality` + `optimize=True`, the optimize helps a little more with image size
  - `webp` + `optimize=True` reduces it alot!
  - `webp` without optimize seems to be the same as with `optimize=True`

Exif Data Image Size test
- https://github.com/python-pillow/Pillow/issues/6804
  - Pillow doesn't save exif data on jpg, webp, tiff. only does it on png images
    - this is probably good for us? that means we only need to remove exif data from png
- Write exif data
  - https://github.com/python-pillow/Pillow/issues/4935
1. Get an image with exif data
   1. easiest way is get an image url that is transformed, because we know Polish doesn't affect image transform urls
   2. Open image in Pillow
   3. Save as jpg/webp with exif metadata
      1. save as jpg
      2. save as jpg with `optimize=True`
      3. save as webp
      4. save as webp with `optimize=True` (this shouldn't make a difference with the first webp)
   4. Strip exif metadata and save:
      1. save as jpg
      2. save as jpg with `optimize=True`
      3. save as webp
      4. save as webp with `optimize=True` (this shouldn't make a difference with the first webp)
So far, these tests on jpeg image show that stripping image metadata on jpeg doesn't change the image size
Maybe find a png image that has exif data
Question for Tim - does removing metadata from images reduce file size?
- https://g.foolcdn.com/editorial/images/548416/mature-senior-woman-sitting-at-table-in-front-of-computer-looking-at-receipts-paying-bills-documents-finance.jpg

```python
>>> img.getexif()
<PIL.Image.Exif object at 0x100969990>
>>> img.save('transformed/senior-woman-with-exif.jpg', exif=img.getexif())
```

https://pillow.readthedocs.io/en/stable/reference/open_files.html#file-handling

## Testing Notes
- file formats supported
- image size supported (CloudFlare hard/soft limits)

## TODAY
- test all things again and make notes
  - have script to run transformations on some images and save it to folder
  - store CloudFlare images in spreadsheet


## Code notes
- Pillow extensions `Image.registered_extensions()`

why is this returning avif??
- `http://g.foolcdn.com/image/?url=https%3A%2F%2Fg.foolcdn.com%2Feditorial%2Fimages%2F519403%2Fgetty-danger-warning-lose-money-mistakes-errors-caution.jpg&w=700&op=resize&format=webp`
- `https://app.datadoghq.com/logs?query=service%3Afoolcdn.com%20%28%28%40http.url_details.host%3Ag.foolcdn.com%20OR%20%40http.url_details.host%3Am.foolcdn.com%29%29%20%20%20%20%20%20%20%20%40http.url_details.queryString.format%3Awebp&additional_filters=%5B%7B%7D%5D&cols=host%2Cservice&event=AQAAAYa61_aoFOPWnQAAAABBWWE2MkdJZUFBRGdoLXJtNFRCV0t3RXU&index=&messageDisplay=inline&stream_sort=time%2Cdesc&viz=stream&from_ts=1676230756265&to_ts=1676317156265&live=true`

- test mutliple of the same query params
- 