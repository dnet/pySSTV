import unittest
from itertools import islice
import pickle
import mock
from mock import MagicMock
from StringIO import StringIO
import hashlib

from sstv import SSTV


class TestSSTV(unittest.TestCase):

    def setUp(self):
        self.s = SSTV(False, 48000, 16)
        self.s.VIS_CODE = 0x00
        self.s.SYNC = 7

    def test_horizontal_sync(self):
        horizontal_sync = self.s.horizontal_sync()
        expected = (1200, self.s.SYNC)
        actual = horizontal_sync.next()
        self.assertEqual(expected, actual)

    def test_gen_freq_bits(self):
        gen_freq_bits = self.s.gen_freq_bits()
        expected = [(1900, 300),
                    (1200, 10),
                    (1900, 300),
                    (1200, 30),
                    (1300, 30),
                    (1300, 30),
                    (1300, 30),
                    (1300, 30),
                    (1300, 30),
                    (1300, 30),
                    (1300, 30),
                    (1300, 30),
                    (1200, 30)]
        actual = list(islice(gen_freq_bits, 0, 1000))
        self.assertEqual(expected, actual)

    # FIXME: Instead of using a test fixture, 'expected' should be synthesized?
    def test_gen_values(self):
        gen_values = self.s.gen_values()
        expected = pickle.load(open("tests/assets/SSTV_gen_values.p"))
        actual = list(islice(gen_values, 0, 1000))
        self.assertEqual(expected, actual)

    def test_gen_samples(self):
        gen_values = self.s.gen_samples()
        # I expected to need this, but I don't? Not in this instance?
        # sstv.random = Mock(return_value=0.4)  # xkcd:221
        expected = pickle.load(open("tests/assets/SSTV_gen_samples.p"))
        actual = list(islice(gen_values, 0, 1000))
        self.assertEqual(expected, actual)

    def test_write_wav(self):
        self.maxDiff = None
        sio = StringIO()
        sio.close = MagicMock()  # ignore close()
        mock_open = MagicMock(return_value=sio)
        with mock.patch('__builtin__.open', mock_open):
            self.s.write_wav('unittest.wav')
        expected = 'bf61c82e96aed1370d5c1753d87729db'
        data = sio.getvalue()
        hash = hashlib.md5()
        hash.update(data)
        actual = hash.hexdigest()
        self.assertEqual(expected, actual)

    def test_init(self):
        self.assertEqual(self.s.image, False)
        self.assertEqual(self.s.samples_per_sec, 48000)
        self.assertEqual(self.s.bits, 16)
