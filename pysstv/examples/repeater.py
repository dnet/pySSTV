#!/usr/bin/env python

"""
Simple repeater that monitors a single directory using inotify, and if
an image appears, it tries to repeat it on using the PyAudio example,
trying to match the mode used for receiving it. It can be tested by
simply copying/linking images to the directory or suing an SSTV
receiver such as slowrx or QSSTV.
"""

from __future__ import print_function
from pyinotify import WatchManager, Notifier, ProcessEvent, IN_CREATE
from pyaudio_sstv import PyAudioSSTV
from pysstv.color import MartinM1, MartinM2, ScottieS1, ScottieS2
from pysstv.grayscale import Robot8BW, Robot24BW
from PIL import Image
from os import path

# matches the abbreviations used by slowrx and QSSTV
MODE_MAP = {
        'M1': MartinM1,
        'M2': MartinM2,
        'S1': ScottieS1,
        'S2': ScottieS2,
        'R8BW': Robot8BW,
        'R24BW': Robot24BW,
        }

class EventHandler(ProcessEvent):
    def process_IN_CREATE(self, event):
        filename = event.pathname
        print('Found image', filename)
        mode = get_module_for_filename(filename)
        img = Image.open(filename)
        if mode is None:
            mode = get_module_for_image(img)
        if mode is None:
            print('No suitable mode found to repeat', filename)
            return
        print('Repeating image using', mode.__name__)
        sstv = mode(img, 44100, 16)
        sstv.vox_enabled = True
        PyAudioSSTV(sstv).execute()

def get_module_for_filename(filename):
    basename, _ = path.splitext(path.basename(filename))
    for mode, module in MODE_MAP.iteritems():
        if mode in basename:
            return module

def get_module_for_image(image):
    size = image.size
    for mode in MODE_MAP.itervalues():
        if all(i >= m for i, m in zip(size, (mode.WIDTH, mode.HEIGHT))):
            return mode

def main():
    from sys import argv, stderr
    try:
        directory = argv[1]
    except IndexError:
        print("Usage: {0} <directory>".format(argv[0]), file=stderr)
    else:
        watch(directory)

def watch(directory):
    wm = WatchManager()
    notifier = Notifier(wm, EventHandler())
    wm.add_watch(directory, IN_CREATE)
    notifier.loop()

if __name__ == '__main__':
    main()
