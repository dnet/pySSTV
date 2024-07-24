#!/usr/bin/env python
from __future__ import division
from pysstv.sstv import byte_to_freq, FREQ_BLACK, FREQ_WHITE, FREQ_VIS_START
from pysstv.grayscale import GrayscaleSSTV
from itertools import chain
from enum import Enum


class Color(Enum):
    red = 0
    green = 1
    blue = 2


class ColorSSTV(GrayscaleSSTV):
    def on_init(self):
        self.pixels = self.image.convert('RGB').load()

    def encode_line(self, line):
        msec_pixel = self.SCAN / self.WIDTH
        image = self.pixels
        for color in self.COLOR_SEQ:
            yield from self.before_channel(color)
            for col in range(self.WIDTH):
                pixel = image[col, line]
                freq_pixel = byte_to_freq(pixel[color.value])
                yield freq_pixel, msec_pixel
            yield from self.after_channel(color)

    def before_channel(self, color):
        return []

    after_channel = before_channel


class MartinM1(ColorSSTV):
    COLOR_SEQ = (Color.green, Color.blue, Color.red)
    VIS_CODE = 0x2c
    WIDTH = 320
    HEIGHT = 256
    SYNC = 4.862
    SCAN = 146.432
    INTER_CH_GAP = 0.572

    def before_channel(self, color):
        if color is Color.green:
            yield FREQ_BLACK, self.INTER_CH_GAP

    def after_channel(self, color):
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

    def before_channel(self, color):
        if color is Color.red:
            yield from MartinM1.horizontal_sync(self)
        yield FREQ_BLACK, self.INTER_CH_GAP


class ScottieS2(ScottieS1):
    VIS_CODE = 0x38
    SCAN = 88.064 - ScottieS1.INTER_CH_GAP
    WIDTH = 160


class ScottieDX(ScottieS1):
    VIS_CODE = 0x4c
    # http://www.barberdsp.com/downloads/Dayton%20Paper.pdf
    SCAN = 345.6000 - ScottieS1.INTER_CH_GAP


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
    INTER_CH_FREQS = [None, FREQ_WHITE, FREQ_BLACK]

    def on_init(self):
        self.yuv = self.image.convert('YCbCr').load()

    def encode_line(self, line):
        pixels = [self.yuv[col, line] for col in range(self.WIDTH)]
        channel = 2 - (line % 2)
        y_pixel_time = self.Y_SCAN / self.WIDTH
        uv_pixel_time = self.C_SCAN / self.WIDTH
        return chain(
                [(FREQ_BLACK, self.SYNC_PORCH)],
                ((byte_to_freq(p[0]), y_pixel_time) for p in pixels),
                [(self.INTER_CH_FREQS[channel], self.INTER_CH_GAP),
                    (FREQ_VIS_START, self.PORCH)],
                ((byte_to_freq(p[channel]), uv_pixel_time) for p in pixels))


class PasokonP3(ColorSSTV):
    """
    [ VIS code or horizontal sync here ]
    Back porch - 5 time units of black (1500 Hz).
    Red component - 640 pixels of 1 time unit each.
    Gap - 5 time units of black.
    Green component - 640 pixels of 1 time unit each.
    Gap - 5 time units of black.
    Blue component - 640 pixels of 1 time unit each.
    Front porch - 5 time units of black.
    Horizontal Sync - 25 time units of 1200 Hz.
    """
    TIMEUNIT = 1000/4800. # ms
    COLOR_SEQ = (Color.red, Color.green, Color.blue)
    VIS_CODE = 0x71
    WIDTH = 640
    HEIGHT = 480+16
    SYNC = 25 * TIMEUNIT
    SCAN = WIDTH * TIMEUNIT
    INTER_CH_GAP = 5 * TIMEUNIT
    
    def before_channel(self, color):
        if color is Color.red:
            yield FREQ_BLACK, self.INTER_CH_GAP

    def after_channel(self, color):
        yield FREQ_BLACK, self.INTER_CH_GAP
        
        
class PasokonP5(PasokonP3):
    TIMEUNIT = 1000/3200. # ms
    VIS_CODE = 0x72
    SYNC = 25 * TIMEUNIT
    SCAN = PasokonP3.WIDTH * TIMEUNIT
    INTER_CH_GAP = 5 * TIMEUNIT
        
class PasokonP7(PasokonP3):
    TIMEUNIT = 1000/2400. # ms
    VIS_CODE = 0xF3
    SYNC = 25 * TIMEUNIT
    SCAN = PasokonP3.WIDTH * TIMEUNIT
    INTER_CH_GAP = 5 * TIMEUNIT


class PD90(ColorSSTV):
    VIS_CODE = 0x63
    WIDTH = 320
    HEIGHT = 256
    SYNC = 20
    PORCH = 2.08
    PIXEL = 0.532

    def gen_image_tuples(self):
        yuv = self.image.convert('YCbCr').load()
        for line in range(0, self.HEIGHT, 2):
            yield from self.horizontal_sync()
            yield FREQ_BLACK, self.PORCH
            pixels0 = [yuv[col, line] for col in range(self.WIDTH)]
            pixels1 = [yuv[col, line + 1] for col in range(self.WIDTH)]
            for p in pixels0:
                yield byte_to_freq(p[0]), self.PIXEL
            for p0, p1 in zip(pixels0, pixels1):
                yield byte_to_freq((p0[2] + p1[2]) / 2), self.PIXEL
            for p0, p1 in zip(pixels0, pixels1):
                yield byte_to_freq((p0[1] + p1[1]) / 2), self.PIXEL
            for p in pixels1:
                yield byte_to_freq(p[0]), self.PIXEL


class PD120(PD90):
    VIS_CODE = 0x5f
    WIDTH = 640
    HEIGHT = 496
    PIXEL = 0.19

class PD160(PD90):
    VIS_CODE = 0x62
    WIDTH = 512
    HEIGHT = 400
    PIXEL = 0.382

class PD180(PD120):
    VIS_CODE = 0x60
    PIXEL = 0.286

class PD240(PD120):
    VIS_CODE = 0x61
    PIXEL = 0.382

class PD290(PD240):
    VIS_CODE = 0x5e
    WIDTH = 800
    HEIGHT = 616
    PIXEL = 0.286


class WraaseSC2180(ColorSSTV):
    VIS_CODE = 0x37
    WIDTH = 320
    HEIGHT = 256
    COLOR_SEQ = (Color.red, Color.green, Color.blue)

    SYNC     = 5.5225
    PORCH    = 0.5
    SCAN     = 235.0

    def before_channel(self, color):
        if color is Color.red:
            yield FREQ_BLACK, self.PORCH
        else:
            return []

    def after_channel(self, color):
        return []


class WraaseSC2120(WraaseSC2180):
    VIS_CODE = 0x3f

    # NB: there are "authoritative" sounding documents that will tell you SC-2
    # 120 uses red and blue channels that have half the line width of the
    # green channel.  Having spent several hours trying to nut out why SC2-120
    # images weren't decoding in anything else, I can say this is utter
    # bunkum.  The line width is the same for all three channels, just
    # shorter.

    SCAN     = 156.0

    def before_channel(self, color):
        # Not sure why, but SC2-120 decoding seems to need an extra few sync
        # pulses to decode in QSSTV and slowrx.  Take the extra pulse out, and
        # it slants something chronic and QSSTV loses sync regularly even on
        # DX mode.  Put it in, and both decode reliably.  Go figure.  SC2-180
        # works just fine without this extra pulse at the start of each
        # channel.
        yield FREQ_BLACK, self.PORCH
        yield from super().before_channel(color)


MODES = (MartinM1, MartinM2, ScottieS1, ScottieS2, ScottieDX, Robot36,
        PasokonP3, PasokonP5, PasokonP7, PD90, PD120, PD160, PD180, PD240,
         PD290, WraaseSC2120, WraaseSC2180)
