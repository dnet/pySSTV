#!/usr/bin/env python

"""
Demonstrates playing the generated samples directly using PyAudio
Tested on PyAudio 0.2.7 http://people.csail.mit.edu/hubert/pyaudio/
"""

from __future__ import division
from pysstv.sstv import SSTV
from time import sleep
from itertools import islice
import struct, pyaudio

class PyAudioSSTV(object):
    def __init__(self, sstv):
        self.pa = pyaudio.PyAudio()
        self.sstv = sstv
        self.fmt = '<' + SSTV.BITS_TO_STRUCT[sstv.bits]

    def __del__(self):
        self.pa.terminate()

    def execute(self):
        self.sampler = self.sstv.gen_samples()
        stream = self.pa.open(
                format=self.pa.get_format_from_width(self.sstv.bits // 8),
                channels=1, rate=self.sstv.samples_per_sec, output=True,
                stream_callback=self.callback)
        stream.start_stream()
        while stream.is_active():
            sleep(0.5)
        stream.stop_stream()
        stream.close()

    def callback(self, in_data, frame_count, time_info, status):
        frames = ''.join(struct.pack(self.fmt, b)
                for b in islice(self.sampler, frame_count))
        return frames, pyaudio.paContinue


def main():
    from PIL import Image
    from pysstv.grayscale import Robot8BW

    img = Image.open("160x120bw.png")
    sstv = Robot8BW(img, 44100, 16)
    sstv.vox_enabled = True
    PyAudioSSTV(sstv).execute()

if __name__ == '__main__':
    main()
