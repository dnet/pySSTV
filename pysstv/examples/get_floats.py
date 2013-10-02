#!/usr/bin/env python

"""
This example streams the raw floating point samples to stdout in 4-byte
single precision format, so that it can be processed outside PySSTV.

Usage example: get_floats.py | play -r 44100 -t f32 -c 1 --norm -
"""

from PIL import Image
from pysstv.grayscale import Robot8BW
import struct, sys

def main():
    img = Image.open("160x120bw.png")
    sstv = Robot8BW(img, 44100, 16)
    sstv.vox_enabled = True
    for value in sstv.gen_values():
        sys.stdout.write(struct.pack('f', value))

if __name__ == '__main__':
    main()
