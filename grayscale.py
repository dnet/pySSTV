#!/usr/bin/env python

from __future__ import division
from sstv import FREQ_BLACK, FREQ_RANGE, FREQ_SYNC, SSTV

class GrayscaleSSTV(SSTV):
	def gen_freq_bits(self):
		for item in SSTV.gen_freq_bits(self):
			yield item
		for line in xrange(self.HEIGHT):
			for item in self.horizontal_sync():
				yield item
			for item in self.encode_line(line):
				yield item

	def horizontal_sync(self):
		yield FREQ_SYNC, self.SYNC

	def encode_line(self, line):
		msec_pixel = self.SCAN / self.WIDTH
		image = self.image
		for col in xrange(self.WIDTH):
			pixel = image.getpixel((col, line))
			value = sum(pixel) / len(pixel)
			freq_pixel = FREQ_BLACK + FREQ_RANGE * value / 255
			yield freq_pixel, msec_pixel


class Robot8BW(GrayscaleSSTV):
	VIS_CODE = 0x02
	WIDTH = 160
	HEIGHT = 120
	SYNC = 10
	SCAN = 56


class Robot24BW(GrayscaleSSTV):
	VIS_CODE = 0x0A
	WIDTH = 320
	HEIGHT = 240
	SYNC = 12
	SCAN = 93
