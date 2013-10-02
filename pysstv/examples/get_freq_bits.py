#!/usr/bin/env python

"""
This example streams the raw floating point (freq, msec) tuples to stdout
in 4-byte single precision format (8 bytes per tuple), so that it can be
processed outside PySSTV.

Usage example using unixsstv/gen_values:
get_freq_bits.py | gen_values 44100 | play -r 44100 -t f32 -c 1 --norm -
"""

from PIL import Image
from pysstv.color import MartinM1
import struct, sys

def main():
    img = Image.open("320x256rgb.png")
    sstv = MartinM1(img, 44100, 16)
    for freq, msec in sstv.gen_freq_bits():
        sys.stdout.write(struct.pack('ff', freq, msec))

if __name__ == '__main__':
    main()
