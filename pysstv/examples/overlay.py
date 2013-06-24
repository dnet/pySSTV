#!/usr/bin/env python

"""
Demonstrates adding text overlay (callsign, RSV, etc.) using PIL
See example output received by slowrx at the following URL:
http://vsza.hu/c6fa52b2c7b20320bdab2da15877f0efbd466e67d37c8d124a557367de9380da.png
"""

from PIL import Image, ImageFont, ImageDraw
from pysstv.grayscale import Robot8BW

img = Image.open("160x120bw.png")
font = ImageFont.load_default()
draw = ImageDraw.Draw(img)
draw.text((0, 0), "HA5VSA", (255,255,255), font=font)
sstv = Robot8BW(img, 44100, 16)
sstv.write_wav("overlay.wav")
