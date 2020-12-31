("""
Usage:
  imgToText.py <imgfile> [--maxHeight=<n>] [--fontSize=<n>] [--colour] [--char=<n>] [--backgroundColour=<#RRGGBB>] [--heightRatio=<n>] [--antialias] [--dither] 
  imgToText.py (-h | --help)
Options:
  -h --help             outputs this information
  -c --colour           outputs image as HTML with colour.
  -a --antialias        resizes image with antialiasing
  -d --dither           dither image colours to web palette.
  --fontSize=<n>        sets the font size of HTML output - default: 8px
  --maxHeight=<n>       resize image so that the height matches maxHeight - default: 100px
  --backgroundColour=<#RRGGBB>  adds specified background colour
  --heightRatio=<n>     resizes image's height by a factor - default: 1.0  
""")

import sys
from docopt import docopt
from PIL import Image
       





def colourBlender(sourceRBG, blendWithRBG):
    # See https://en.wikipedia.org/wiki/Alpha_compositing - section on "Alpha Blending"
    conversion = 255.0
    sourceRBGFactor = (sourceRBG[3] / conversion)
    blendWithRBGFactor = (blendWithRBG[3] / conversion) * (1 - sourceRBGFactor)
    result_alpha = sourceRBGFactor + blendWithRBGFactor

    if result_alpha == 0:       # accounts for division by zero
        return (0, 0, 0, 0)
    else:
        return (
            int(((sourceRBG[0] * sourceRBGFactor) + (blendWithRBG[0] * blendWithRBGFactor)) / result_alpha), 
            int(((sourceRBG[1] * sourceRBGFactor) + (blendWithRBG[1] * blendWithRBGFactor)) / result_alpha),
            int(((sourceRBG[2] * sourceRBGFactor) + (blendWithRBG[2] * blendWithRBGFactor)) / result_alpha),
            int(result_alpha * conversion) 
        ) 

def createGrayscaleImage(pixels, width, height, backgroundColour):

    # grayscale
    colour = "@MNZQUzj?+>;*-. "

    string = ""
    # first go through the height,  otherwise will rotate
    for h in range(height):
        for w in range(width):

            rgba = pixels[w, h]

            # If partial transparency and we have a backgroundColour, combine with bg
            # colour
            if rgba[3] != 255 and backgroundColour is not None:
                rgba = colourBlender(rgba, backgroundColour)

            # Throw away any alpha (either because backgroundColour was partially
            # transparent or had no bg colour)
            # Could make a case to choose character to draw based on alpha but
            # not going to do that now...
            rgb = rgba[:3]

            string += colour[int(sum(rgb) / 3.0 / 256.0 * 16)]
            #string += colour[int(sum(rgb) / 3.0 / 256.0 * 16)] # mc

        string += "\n"

    return string


def loadImageResized(imageName, antialias, maxHeight, widthAspectRatio):

    if widthAspectRatio is None:
        widthAspectRatio = 1.0

    img = Image.open(imageName)

    # force image to RGBA - deals with palettized images (e.g. gif) etc.
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # need to change the size of the image?
    if maxHeight is not None or widthAspectRatio != 1.0:

        oldWidth, oldHeight = img.size

        newWidth = oldWidth
        newHeight = oldHeight

        # First apply aspect ratio change (if any) - just need to adjust one axis
        # so we'll do the height.
        if widthAspectRatio != 1.0:
            newHeight = int(float(widthAspectRatio) * newHeight)

        # Now isotropically resize up or down (preserving aspect ratio) such that 
        # longer side of image is maxHeight 
        if maxHeight is not None:
            rate = float(maxHeight) / newHeight
            newWidth = int(rate * newWidth)  
            newHeight = int(rate * newHeight)

        if oldWidth != newWidth or oldHeight != newHeight:
            img = img.resize((newWidth, newHeight), Image.ANTIALIAS if antialias else Image.NEAREST)

    return img


def floydsteinbergDitherToWebPalette(img):
    if img.mode != 'RGB': 
        img = img.convert('RGB')     
    img = img.convert(mode="P", matrix=None, dither=Image.FLOYDSTEINBERG, palette=Image.WEB, colors=256)
    img = img.convert('RGBA')    
    return img


def ditherImageToWebPalette(img, backgroundColour):
    
    if backgroundColour is not None:
        # We know the background colour so flatten the image and bg colour together, thus getting rid of alpha
        # This is important because as discussed below, dithering alpha doesn't work correctly.
        img = Image.alpha_composite(Image.new("RGBA", img.size, backgroundColour), img)  # alpha blend onto image filled with backgroundColour
        ditheredImage = floydsteinbergDitherToWebPalette(img)    
    else:
        
        # Force image to RGBA if it isn't already - simplifies the rest of the code    
        if img.mode != 'RGBA': 
            img = img.convert('RGBA')    

        rgb_img = img.convert('RGB')    
    
        orig_pixels = img.load()
        rgb_pixels = rgb_img.load()
        width, height = img.size

        for h in range(height):    # set transparent pixels to black
            for w in range(width):
                if (orig_pixels[w, h])[3] != 255:    
                    rgb_pixels[w, h] = (0, 0, 0)   # bashing in a new value changes it!

        ditheredImage = floydsteinbergDitherToWebPalette(rgb_img)    

        dithered_pixels = ditheredImage.load() # must do it again
        
        for h in range(height):    # restore original RGBA for transparent pixels
            for w in range(width):
                if (orig_pixels[w, h])[3] != 255:    
                    dithered_pixels[w, h] = orig_pixels[w, h]   # bashing in a new value changes it!

    return ditheredImage

def createColouredImage(pixels, width, height, htmlChar):

    string = ""

    # first go through the height,  otherwise will rotate
    for h in range(height):
        for w in range(width):

            rgba = pixels[w, h]

            string += ("<span style=\"color:rgba({0}, {1}, {2}, {3});\">" + 
                htmlChar + "</span>").format(rgba[0], rgba[1], rgba[2], rgba[3] / 255.0)

        string += "\n"

    return string


""" #RRGGBB --> (R, G, B) tuple """
def HTMLcolourToRGB(colourString):
    colourString = colourString.strip()
    if colourString[0] == '#':
        colourString = colourString[1:]
    if len(colourString) != 6:
        raise ValueError("input #{0} is not in #RRGGBB format".format(colourString))

    r, g, b = colourString[:2], colourString[2:4], colourString[4:]
    # convert hexadecimal strings into numbers
    r, g, b = [int(n, 16) for n in (r, g, b)]
    return (r, g, b)

if __name__ == '__main__':

    dct = docopt(__doc__)
    imageName = dct['<imgfile>']
    maxHeight = dct['--maxHeight']
    htmlChar = dct['--char']
    coloured = dct['--colour']
    fontSize = dct['--fontSize']
    backgroundColour = dct['--backgroundColour']
    antialias = dct['--antialias']
    dither = dct['--dither']
    heightRatioFactor = dct['--heightRatio']

    try:
        maxHeight = float(maxHeight)
    except:
        maxHeight = 150.0   # default maxHeight: 100px

    try:
        fontSize = int(fontSize)
    except:
        fontSize = 8

    try:
        if ((htmlChar is None) or (htmlChar == "")):
            raise ValueError("bad HTML char")

        htmlChar = str(htmlChar)
    except:
        htmlChar = "&#9607;"

    try:
        # add fully opaque alpha value (255)
        backgroundColour = HTMLcolourToRGB(backgroundColour) + (255, )
    except:
        backgroundColour = None

    try:
        heightRatioFactor = float(heightRatioFactor)
    except:
        heightRatioFactor = 1.0   # default heightRatioFactor: 1.0

    try:
        img = loadImageResized(imageName, antialias, maxHeight, heightRatioFactor)
    except IOError:
        exit("File not found: " + imageName)

    # Dither _after_ resizing
    if dither:
        img = ditherImageToWebPalette(img, backgroundColour)

    # get pixels
    pixel = img.load()

    width, height = img.size

    if coloured:
        string = createColouredImage(pixel, width, height, htmlChar)
    else:
        string = createGrayscaleImage(
            pixel, width, height, backgroundColour)


    template = """<!DOCTYPE HTML>
    <html>
    <head>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <style type="text/css" media="all">
        pre {
            white-space: pre-wrap;       /* css */
            white-space: -moz-pre-wrap;  /* Mozilla */
            white-space: -pre-wrap;      /* Opera */
            white-space: -o-pre-wrap;    /* Opera */
            word-wrap: break-word;       /* Internet Explorer */
            font-family: 'Menlo', 'Courier New', 'Consola';
            line-height: 1.0;
            font-size: %dpx;
        }
        </style>
    </head>
    <body>
        <pre>%s</pre>
    </body>
    </html>
    """

    html = template % (fontSize, string)

    f = open("output.html", "w")
    f.write(html)
    f.close()


    