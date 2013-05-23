#!/usr/bin/env python

from __future__ import division, with_statement
from math import sin, pi
from random import random
import struct

FREQ_VIS_BIT1 = 1100
FREQ_SYNC = 1200
FREQ_VIS_BIT0 = 1300
FREQ_BLACK = 1500
FREQ_VIS_START = 1900
FREQ_WHITE = 2300
FREQ_RANGE = FREQ_WHITE - FREQ_BLACK

MSEC_VIS_START = 300
MSEC_VIS_SYNC = 10
MSEC_VIS_BIT = 30

ROBOT_BW_8_WIDTH = 160
ROBOT_BW_8_HEIGHT = 120
ROBOT_BW_8_SYNC = 10
ROBOT_BW_8_SCAN = 56
ROBOT_BW_8_VIS = 0x02

class SSTV(object):
	def __init__(self, image, samples_per_sec, bits):
		self.image = image
		self.samples_per_sec = samples_per_sec
		self.bits = bits

	BITS_TO_STRUCT = {8: 'b', 16: 'h'}
	def write_wav(self, filename):
		bytes_per_sec = self.bits // 8
		fmt = '<' + self.BITS_TO_STRUCT[self.bits]
		data = ''.join(struct.pack(fmt, b) for b in self.gen_samples())
		payload = ''.join((
				'WAVE',
				'fmt ',
				struct.pack('<IHHIIHH', 16, 1, 1, self.samples_per_sec,
					self.samples_per_sec * bytes_per_sec, bytes_per_sec,
					self.bits),
				'data',
				struct.pack('<I', len(data))
				))
		header = 'RIFF' + struct.pack('<I', len(payload) + len(data))
		with file(filename, 'wb') as wav:
			wav.write(header)
			wav.write(payload)
			wav.write(data)

	def gen_samples(self):
		"""generates bits from gen_values"""
		max_value = 2 ** self.bits
		alias = 1 / max_value
		amp = max_value / 2
		lowest = -amp
		highest = amp - 1
		for value in self.gen_values():
			sample = int(round(value * amp + alias * random()))
			yield max(min(highest, sample), lowest)

	def gen_values(self):
		"""generates -1 .. +1 values from freq_bits"""
		spms = self.samples_per_sec / 1000
		param = 0
		for freq, msec in self.gen_freq_bits():
			offset = param
			for sample in xrange(int(round(spms * msec + random()))):
				t = sample / self.samples_per_sec
				param = t * freq * 2 * pi + offset
				yield sin(param)

	def gen_freq_bits(self):
		"""generates (freq, msec) tuples from image"""
		yield FREQ_VIS_START, MSEC_VIS_START
		yield FREQ_SYNC, MSEC_VIS_SYNC
		yield FREQ_VIS_START, MSEC_VIS_START
		yield FREQ_SYNC, MSEC_VIS_BIT # start bit
		vis_code = ROBOT_BW_8_VIS
		num_ones = 0
		for bitnum in xrange(7):
			bit = (vis_code >> bitnum) & 1
			num_ones += bit
			bit_freq = FREQ_VIS_BIT1 if bit == 1 else FREQ_VIS_BIT0
			yield bit_freq, MSEC_VIS_BIT
		parity_freq = FREQ_VIS_BIT1 if num_ones % 2 == 1 else FREQ_VIS_BIT0
		yield parity_freq, MSEC_VIS_BIT
		yield FREQ_SYNC, MSEC_VIS_BIT # stop bit
		msec_pixel = ROBOT_BW_8_SCAN / ROBOT_BW_8_WIDTH
		image = self.image
		for line in xrange(ROBOT_BW_8_HEIGHT):
			yield FREQ_SYNC, ROBOT_BW_8_SYNC
			for col in xrange(ROBOT_BW_8_WIDTH):
				pixel = image.getpixel((col, line))
				value = sum(pixel) / len(pixel)
				freq_pixel = FREQ_BLACK + FREQ_RANGE * value / 256
				yield freq_pixel, msec_pixel


if __name__ == '__main__':
	from PIL import Image
	image = Image.open('160x120bw.png')
	s = SSTV(image, 48000, 16)
	s.write_wav('test.wav')
