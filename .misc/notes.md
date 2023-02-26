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
  - how to handle values that exceed limits? throw an error like `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?blur=300`
- brightness - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?brightness=2.0`
  - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?brightness=10.0`
  - value keeps increasing brightness, no max...try with 2.0 and 10.0
  - brightness applied after fit=pad
- contrast - `https://m.foolcdn.com/media/affiliates/original_images/GettyImages-1196980264_K3vqKMF.jpg?contrast=10.0`
  - value keeps increasing contrast, no max...try with 2.0 and 10.0
- height and width
  - `https://g.foolcdn.com/image/?url=https%3A%2F%2Fg.foolcdn.com%2Feditorial%2Fimages%2F711554%2Fa-hand-drawing-money-signs-and-an-upward-arrow-on-a-chalkboard.jpg&h=104&w=184`
- fit cover
  - if you pass it dimensions different than aspect ratio, it will crop to fit
    - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?width=1600&height=2400&fit=cover`
  - 
- Combination
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?blur=250&fit=pad&width=2000&height=2000`
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=0.2&fit=pad&width=2500&height=3000`
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?brightness=10&fit=pad&width=2500&height=3000&background=%23FF3333` (red background)
    - brightness is applied after fit=pad (background gets brighter)
  - `https://m.foolcdn.com/media/affiliates/original_images/woman_with_phone_and_laptop_EF0nQi5.jpg?contrast=10&fit=pad&width=2500&height=3000&background=%23FF3333`
    - contrast applied after fit=pad (background is not contrasted!)


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
- cropping centering - https://www.pythoninformer.com/python-libraries/pillow/imageops-resizing/

## Thoughts
- cache webp/avif versions?
- warm cache before cutover
- cloudflare worker limits - https://developers.cloudflare.com/workers/platform/limits/
  - https://developers.cloudflare.com/images/image-resizing/format-limitations/#format-limitations
  - not sure why this image doesn't scale greater than dpr=3 - `https://g.foolcdn.com/image/?url=https%3A%2F%2Fg.foolcdn.com%2Feditorial%2Fimages%2F711554%2Fa-hand-drawing-money-signs-and-an-upward-arrow-on-a-chalkboard.jpg&h=104&w=184&dpr=3`