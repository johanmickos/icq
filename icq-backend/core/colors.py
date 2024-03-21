"""
Color conversion functions.
"""
import numpy as np
import numpy.typing as nptyping
import skimage.color

RGB = nptyping.NDArray      # e.g. [255, 255, 255]
LAB = nptyping.NDArray      # e.g. [100, 0  , 0  ]
HEX = str                   # e.g. #FFFFFF

def rgb2hex(r: int, g: int, b: int) -> HEX:
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def hex2rgb(hex: HEX)->RGB:
    hex = hex.lstrip('#')
    return np.array([int(hex[i:i+2], 16) for i in (0, 2, 4)])


def hex2lab(hex: HEX)->LAB:
    rgb = hex2rgb(hex)
    return rgb2lab(rgb)


def lab2rgb(lab: LAB)->RGB:
    rgb = (skimage.color.lab2rgb(lab.astype(float))*255).astype(int)
    return np.array([rgb[0], rgb[1], rgb[2]])


def lab2hex(lab: LAB)->HEX:
    return rgb2hex(*lab2rgb(lab))


def rgb2lab(rgb: RGB)->LAB:
    rgb_scaled = np.round(rgb/255, 2)
    lab = skimage.color.rgb2lab(rgb_scaled)
    return lab

def distance_rgb(a: RGB, b: RGB)->float:
    return float(np.linalg.norm(skimage.color.rgb2lab(a/255) - skimage.color.rgb2lab(b/255)))

def distance_lab(a: LAB, b: LAB)->float:
    return distance_rgb(rgb2lab(a), rgb2lab(b))
