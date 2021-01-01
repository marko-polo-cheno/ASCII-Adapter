("""
Usage:
  imgToText.py <imgfile> [--maxHeight=<n>] [--fontSize=<n>] [--colour] [--char=<n>] [--backgroundColour=<#RRGGBB>] [--heightRatio=<n>] [--antialias] [--dither] 
  imgToText.py (-h | --help)
Options:
  -h --help             outputs this information
  -c --colour           outputs image as HTML with colour.
  -a --antialias        resizes image with antialiasing
  -d --dither           dither image colours to web palette.
  --char=<n>            sets the character to use in the HTML representation - default: "&#9607;" a whole character's dedicated space
  --fontSize=<n>        sets the font size of HTML output - default: 8px
  --maxHeight=<n>       resize image so that the height matches maxHeight - default: 100px
  --backgroundColour=<#RRGGBB>  adds specified background colour
  --heightRatio=<n>     resizes image's height by a factor - default: 1.0  
""")

import sys
from docopt import docopt
from PIL import Image


def colourBlender(sourceRBG, blendWithRBG):
    # See https://en.wikipedia.org/wiki/Alpha_compositing
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

    choiceFactor = float(len(colour)) / 3.0 / 256.0

    output = ""
    # go thru pixels line by line
    for h in range(height):
        for w in range(width):

            rgba = pixels[w, h]

            # If transparency and has backgroundColour, combine with background colour
            if rgba[3] != 255 and backgroundColour is not None:
                rgba = colourBlender(rgba, backgroundColour)

            # Rid of alpha
            rgb = rgba[:3]

            output += colour[int(sum(rgb) * choiceFactor)]

        output += "\n"

    return output


def loadImageResized(imageName, antialias, maxHeight, widthAspectRatio):

    if widthAspectRatio is None:
        widthAspectRatio = 1.0

    img = Image.open(imageName)

    # force image to RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # change image size if needed
    if maxHeight is not None or widthAspectRatio != 1.0:

        oldWidth, oldHeight = img.size

        newWidth = oldWidth
        newHeight = oldHeight

        # Aspect ratio change
        if widthAspectRatio != 1.0:
            newHeight = int(float(widthAspectRatio) * newHeight)

        # Resize based on max height
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
        img = Image.alpha_composite(Image.new("RGBA", img.size, backgroundColour), img)  # alpha blend onto image filled with backgroundColour
        ditheredImage = floydsteinbergDitherToWebPalette(img)    
    else:
        
        # RGBA if it isn't already - simplifies the rest of the code    
        if img.mode != 'RGBA': 
            img = img.convert('RGBA')    

        rbgImg = img.convert('RGB')    
    
        originalPixels = img.load()
        colouredPixels = rbgImg.load()
        width, height = img.size

        for h in range(height):    # set transparent pixels to black
            for w in range(width):
                if (originalPixels[w, h])[3] != 255:    
                    colouredPixels[w, h] = (0, 0, 0)   # set to black

        ditheredImage = floydsteinbergDitherToWebPalette(rbgImg)    

        ditheredPixels = ditheredImage.load() # do it again
        
        for h in range(height):    # restore original RGBA for transparent pixels
            for w in range(width):
                if (originalPixels[w, h])[3] != 255:    
                    ditheredPixels[w, h] = originalPixels[w, h]   # restore

    return ditheredImage


def createColouredImage(pixels, width, height, htmlChar):

    output = ""

    # For every pixel, make a coressponding coloured character
    for h in range(height):
        for w in range(width):

            # RBGA tuple
            rgba = pixels[w, h]

            # Coloured character HTML
            output += ("<span style=\"color:rgba({0}, {1}, {2}, {3});\">" + htmlChar + 
                "</span>").format(rgba[0], rgba[1], rgba[2], rgba[3] / 255.0)

        output += "\n"

    return output


""" #RRGGBB --> (R, G, B) tuple """
def HTMLcolourToRGB(colourString):
    colouroutput = colourString.strip()
    
    if colourString[0] == '#':
        colouroutput = colourString[1:]
    if len(colourString) != 6:
        raise ValueError("the input #{0} needs to be in #RRGGBB format".format(colourString))

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
        output = createColouredImage(pixel, width, height, htmlChar)
    else:
        output = createGrayscaleImage(
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

    html = template % (fontSize, output)

    f = open("output.html", "w")
    f.write(html)
    f.close()


    