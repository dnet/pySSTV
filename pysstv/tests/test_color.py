import unittest
from itertools import islice
import pickle

from PIL import Image

from pysstv import color
from pysstv.tests.common import get_asset_filename


class TestMartinM1(unittest.TestCase):

    def setUp(self):
        self.image = Image.new('RGB', (320, 256))
        self.s = color.MartinM1(self.image, 48000, 16)
        lena = Image.open(get_asset_filename('320x256.png'))
        self.lena = color.MartinM1(lena, 48000, 16)

    def test_gen_freq_bits(self):
        expected = pickle.load(open(get_asset_filename("MartinM1_freq_bits.p")))
        actual = list(islice(self.s.gen_freq_bits(), 0, 1000))
        self.assertEqual(expected, actual)

    def test_gen_freq_bits_lena(self):
        expected = pickle.load(open(get_asset_filename("MartinM1_freq_bits_lena.p")))
        actual = list(islice(self.lena.gen_freq_bits(), 0, 1000))
        self.assertEqual(expected, actual)

    def test_encode_line(self):
        zeroth = list(self.s.encode_line(0))
        first = list(self.s.encode_line(1))
        tenth = list(self.s.encode_line(10))
        eleventh = list(self.s.encode_line(11))

        self.assertEqual(zeroth, first)
        self.assertEqual(tenth, eleventh)
        self.assertEqual(zeroth, eleventh)

    def test_encode_line_lena(self):
        self.maxDiff = None
        line_numbers = [1, 10, 100]
        for line in line_numbers:
            file = open(get_asset_filename("MartinM1_encode_line_lena%d.p" % line))
            expected = pickle.load(file)
            actual = list(self.lena.encode_line(line))
            self.assertEqual(expected, actual)
