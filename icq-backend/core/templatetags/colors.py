import numpy as np
import skimage.color
from core.colors import LAB, distance_lab
from django import template

register = template.Library()

@register.filter
def colorsort(values):
    """Sorts the values by their LAB distance from the color white"""
    def distance(v):
        a = v.color_lab
        ref = np.array([100, 0,0 ])
        return np.linalg.norm(a-ref)
    return sorted(values, key=distance)

@register.filter
def lightness(value, arg):
    value = value.copy()
    if isinstance(arg, str):
        arg = arg.strip()
    if isinstance(arg, str) and arg.endswith('%'):
        arg = float(arg[:-1]) / 100.0
    else:
        arg = float(arg)
    ret = value * arg
    return ret.astype(int)

@register.filter
def contrast(value):
    # Compute color brightness to determine whether to lighten or darken output
    # See https://www.w3.org/WAI/ER/WD-AERT/#color-contrast
    c = value[0]*0.299 + value[1]*0.587 + value[2]*0.114
    c /= 255
    c -= 0.5

    # c is now [-1, 1]
    scaled = (-1)*( 0.0001 * pow(c, 3)) + pow(c, 2) + 0.2
    print(value, c, scaled)
    return lightness(value, scaled).astype(int)
