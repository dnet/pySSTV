#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# copy to ~/.gimp-2.8/plug-ins/
# dependencies: GIMP 2.8, python-imaging-tk

from gimpfu import register, main, pdb, PF_BOOL, PF_STRING, PF_RADIO
from tempfile import mkstemp
from PIL import Image, ImageTk
from Tkinter import Tk, Canvas, Button, Checkbutton, IntVar, Frame, LEFT, NW
from pysstv import __main__ as pysstv_main
from pysstv.examples.pyaudio_sstv import PyAudioSSTV
from pysstv.sstv import SSTV
from itertools import repeat
from threading import Thread
import os

MODULE_MAP = pysstv_main.build_module_map()

class AudioThread(Thread):
    def __init__(self, sstv, parent):
        Thread.__init__(self)
        self.pas = PyAudioSSTV(sstv)
        self.parent = parent

    def run(self):
        self.pas.execute()
        self.parent.audio_thread_ended()

    def stop(self):
        self.pas.sampler = []
        self.pas = None


class Sine1750(SSTV):
    encode_line = None

    def gen_freq_bits(self):
        return repeat((1750, 1000))


class Transmitter(object):
    def __init__(self, sstv, root, progress):
        def encode_line_hooked(line):
            progress.update_image(line)
            return self.original_encode_line(line)
        self.progress = progress
        self.sstv = sstv
        self.original_encode_line = sstv.encode_line
        sstv.encode_line = encode_line_hooked
        self.root = root
        self.tx_enabled = IntVar()
        self.audio_thread = None

    def start_stop_tx(self):
        if self.tx_enabled.get():
            self.audio_thread = AudioThread(self.sstv, self)
            self.audio_thread.start()
        elif self.audio_thread is not None:
            self.audio_thread.stop()
            self.progress.update_image()

    def audio_thread_ended(self):
        self.tx_enabled.set(0)

    def close(self):
        self.root.destroy()


class ProgressCanvas(Canvas):
    def __init__(self, master, image):
        width, height = image.size
        if height / float(width) > 1.5:
            width *= 2
        elif width < 200:
            width *= 2
            height *= 2
        if (width, height) != image.size:
            image = image.resize((width, height))
        pixels = image.load()
        RED, GREEN, BLUE = range(3)
        self.colors = ['#{0:02x}{1:02x}{2:02x}'.format(
            255 - sum(pixels[x, y][RED]   for x in xrange(width)) / width,
            255 - sum(pixels[x, y][GREEN] for x in xrange(width)) / width,
            255 - sum(pixels[x, y][BLUE]  for x in xrange(width)) / width)
            for y in xrange(height)]
        Canvas.__init__(self, master, width=width, height=height)
        self.tk_img = ImageTk.PhotoImage(image)
        self.update_image()

    def update_image(self, line=None):
        image = self.tk_img
        self.create_image(0, 0, anchor=NW, image=image)
        if line is not None:
            self.create_line(0, line, image.width(), line, fill=self.colors[line])


def transmit_current_image(image, drawable, mode, vox, fskid):
    sstv = MODULE_MAP[mode]
    handle, png_fn = mkstemp(suffix='.png', prefix='pysstv-gimp-')
    os.fdopen(handle).close()
    try:
        pdb.gimp_file_save(image, drawable, png_fn, png_fn)
        pil_img = Image.open(png_fn)
        sstv_size = sstv.WIDTH, sstv.HEIGHT
        if pil_img.size != sstv_size:
            pil_img = pil_img.resize(sstv_size, Image.ANTIALIAS)
        if 'grayscale' in sstv.__module__:
            pil_img = pil_img.convert('LA').convert('RGB')
        root = Tk()
        s = sstv(pil_img, 44100, 16)
        s.vox_enabled = vox
        if fskid:
            s.add_fskid_text(fskid)
        pc = ProgressCanvas(root, pil_img)
        pc.pack()
        tm = Transmitter(s, root, pc)
        tm1750 = Transmitter(Sine1750(None, 44100, 16), None, None)
        buttons = Frame(root)
        for text, tram in (('TX', tm), ('1750 Hz', tm1750)):
            Checkbutton(buttons, text=text, indicatoron=False, padx=5, pady=5,
                    variable=tram.tx_enabled, command=tram.start_stop_tx).pack(side=LEFT)
        Button(buttons, text="Close", command=tm.close).pack(side=LEFT)
        buttons.pack()
        root.mainloop()
    finally:
        os.remove(png_fn)

register(
        "pysstv_for_gimp",
        "PySSTV for GIMP",
        "Transmits the current image using PySSTV",
        "Andras Veres-Szentkiralyi",
        "Andras Veres-Szentkiralyi",
        "November 2013",
        "<Image>/PySSTV/Transmit...",
        "*",
        [
            (PF_RADIO, "mode", "SSTV mode", "MartinM1",
                tuple((n, n) for n in sorted(MODULE_MAP.iterkeys()))),
            (PF_BOOL, "vox", "Include VOX tones", True),
            (PF_STRING, "fskid", "FSK ID", ""),
        ],
        [],
        transmit_current_image
        )

main()
