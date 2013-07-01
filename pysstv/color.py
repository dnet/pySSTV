#!/usr/bin/env python

from __future__ import division
from sstv import byte_to_freq, FREQ_BLACK
from grayscale import GrayscaleSSTV


class ColorSSTV(GrayscaleSSTV):
    RED, GREEN, BLUE = range(3)

    def encode_line(self, line):
        cs = self.COLOR_SEQ
        msec_pixel = self.SCAN / self.WIDTH
        image = self.image.load()
        for index in cs:
            for item in self.before_channel(index):
                yield item
            for col in xrange(self.WIDTH):
                pixel = image[col, line]
                freq_pixel = byte_to_freq(pixel[index])
                yield freq_pixel, msec_pixel
            for item in self.after_channel(index):
                yield item

    def before_channel(self, index):
        return []

    after_channel = before_channel


class MartinM1(ColorSSTV):
    COLOR_SEQ = (ColorSSTV.GREEN, ColorSSTV.BLUE, ColorSSTV.RED)
    VIS_CODE = 0x2c
    WIDTH = 320
    HEIGHT = 256
    SYNC = 4.862
    SCAN = 146.432
    INTER_CH_GAP = 0.572

    def before_channel(self, index):
        if index == ColorSSTV.GREEN:
            yield FREQ_BLACK, self.INTER_CH_GAP

    def after_channel(self, index):
        yield FREQ_BLACK, self.INTER_CH_GAP


class MartinM2(MartinM1):
    VIS_CODE = 0x28
    WIDTH = 160
    SCAN = 73.216


class ScottieS1(MartinM1):
    VIS_CODE = 0x3c
    SYNC = 9
    INTER_CH_GAP = 1.5
    SCAN = 138.24 - INTER_CH_GAP

    def horizontal_sync(self):
        return []

    def before_channel(self, index):
        if index == ColorSSTV.RED:
            for item in MartinM1.horizontal_sync(self):
                yield item
        yield FREQ_BLACK, self.INTER_CH_GAP


class ScottieS2(ScottieS1):
    VIS_CODE = 0x38
    SCAN = 88.064 - ScottieS1.INTER_CH_GAP
    WIDTH = 160

MODES = (MartinM1, MartinM2, ScottieS1, ScottieS2)
