#!/usr/bin/env python

from __future__ import division
from sstv import byte_to_freq, FREQ_BLACK, FREQ_WHITE, FREQ_VIS_START
from grayscale import GrayscaleSSTV
from itertools import chain


RED, GREEN, BLUE = range(3)

class ColorSSTV(GrayscaleSSTV):
    def encode_line(self, line):
        msec_pixel = self.SCAN / self.WIDTH
        image = self.image.load()
        for index in self.COLOR_SEQ:
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
    COLOR_SEQ = (GREEN, BLUE, RED)
    VIS_CODE = 0x2c
    WIDTH = 320
    HEIGHT = 256
    SYNC = 4.862
    SCAN = 146.432
    INTER_CH_GAP = 0.572

    def before_channel(self, index):
        if index == GREEN:
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


class Robot36(ColorSSTV):
    VIS_CODE = 0x08
    WIDTH = 320
    HEIGHT = 240
    SYNC = 9
    INTER_CH_GAP = 4.5
    Y_SCAN = 88
    C_SCAN = 44
    PORCH = 1.5
    SYNC_PORCH = 3
    INTER_CH_FREQS = [FREQ_BLACK, FREQ_WHITE]
    CHANNEL_COEFFS = [
            (128.0, 112.439, -94.154, -18.285),
            (128.0, -37.945, -74.494, 112.439)]

    def encode_line(self, line):
        image = self.image.load()
        pixels = [image[col, line] for col in xrange(self.WIDTH)]
        channel = line % 2
        return chain(
                [(FREQ_BLACK, self.SYNC_PORCH)],
                encode_robot_pixels(pixels, (16.0, 65.738, 129.057, 25.064),
                    self.Y_SCAN / self.WIDTH),
                [(self.INTER_CH_FREQS[channel], self.INTER_CH_GAP),
                    (FREQ_VIS_START, self.PORCH)],
                encode_robot_pixels(pixels, self.CHANNEL_COEFFS[channel],
                    self.C_SCAN / self.WIDTH))

def encode_robot_pixels(pixels, coeffs, pixel_time):
    cs, cr, cg, cb = coeffs
    for pixel in pixels:
        value = cs + (0.003906 * ((cr * pixel[RED]) +
            (cg * pixel[GREEN]) + (cb * pixel[BLUE])))
        yield byte_to_freq(value), pixel_time


MODES = (MartinM1, MartinM2, ScottieS1, ScottieS2, Robot36)
