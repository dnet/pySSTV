#!/usr/bin/env python

from __future__ import division, with_statement
from math import sin, pi, floor
from random import random
from contextlib import closing
import struct, wave

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

class SSTV(object):
	def __init__(self, image, samples_per_sec, bits):
		self.image = image
		self.samples_per_sec = samples_per_sec
		self.bits = bits

	BITS_TO_STRUCT = {8: 'b', 16: 'h'}
	def write_wav(self, filename):
		"""writes the whole image to a Microsoft WAV file"""
		fmt = '<' + self.BITS_TO_STRUCT[self.bits]
		data = ''.join(struct.pack(fmt, b) for b in self.gen_samples())
		with closing(wave.open(filename, 'wb')) as wav:
			wav.setnchannels(1)
			wav.setsampwidth(self.bits // 8)
			wav.setframerate(self.samples_per_sec)
			wav.writeframes(data)

	def gen_samples(self):
		"""generates discrete samples from gen_values(), performing quantization according to the bits per sample value given during construction
		"""
		max_value = 2 ** self.bits
		alias = 1 / max_value
		amp = max_value / 2
		lowest = -amp
		highest = amp - 1
		for value in self.gen_values():
			sample = int(round(value * amp + alias * (random() - 0.5)))
			yield max(min(highest, sample), lowest)

	def gen_values(self):
		"""generates samples between -1 and +1 from gen_freq_bits(), performing sampling according to the samples per second value given during construction
		"""
		spms = self.samples_per_sec / 1000
		param = 0
		samples = 0
		for freq, msec in self.gen_freq_bits():
			offset = param
			samples += spms * msec
			tx = floor(samples)
			for sample in xrange(int(tx)):
				t = sample / self.samples_per_sec
				param = t * freq * 2 * pi + offset
				yield sin(param)
			samples -= tx

	def gen_freq_bits(self):
		"""generates tuples (freq, msec) that describe a sine wave segment with frequency in Hz and duration in ms
		"""
		yield FREQ_VIS_START, MSEC_VIS_START
		yield FREQ_SYNC, MSEC_VIS_SYNC
		yield FREQ_VIS_START, MSEC_VIS_START
		yield FREQ_SYNC, MSEC_VIS_BIT # start bit
		vis = self.VIS_CODE
		num_ones = 0
		for _ in xrange(7):
			bit = vis & 1
			vis >>= 1
			num_ones += bit
			bit_freq = FREQ_VIS_BIT1 if bit == 1 else FREQ_VIS_BIT0
			yield bit_freq, MSEC_VIS_BIT
		parity_freq = FREQ_VIS_BIT1 if num_ones % 2 == 1 else FREQ_VIS_BIT0
		yield parity_freq, MSEC_VIS_BIT
		yield FREQ_SYNC, MSEC_VIS_BIT # stop bit

	def horizontal_sync(self):
		yield FREQ_SYNC, self.SYNC


def byte_to_freq(value):
	return FREQ_BLACK + FREQ_RANGE * value / 255
