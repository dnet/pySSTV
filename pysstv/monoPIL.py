#!/usr/bin/env python

"""primitive partial PIL to IronPython (.Net) wrapper"""

import clr
clr.AddReference("System.Drawing")
from System.Drawing import Image as SDI

class Image(object):
	@classmethod
	def open(_cls, filename):
		return Image(SDI.FromFile(filename))

	def __init__(self, img):
		self.img = img
		self.size = (img.Width, img.Height)
	
	def convert(self, _ignore):
		return self # TODO

	def load(self):
		return self

	def __getitem__(self, (x, y)):
		color = self.img.GetPixel(x, y)
		return int(color.R), int(color.G), int(color.B)
