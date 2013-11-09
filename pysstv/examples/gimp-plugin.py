#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# copy to ~/.gimp-2.8/plug-ins/
# dependencies: GIMP 2.8, python-imaging-tk

from gimpfu import register, main, pdb, PF_BOOL, PF_STRING, PF_RADIO, CLIP_TO_IMAGE
from PIL import Image, ImageTk
from Tkinter import Tk, Canvas, Button, Checkbutton, IntVar, Frame, LEFT, NW
from pysstv import __main__ as pysstv_main
from pysstv.examples.pyaudio_sstv import PyAudioSSTV
from pysstv.sstv import SSTV
from itertools import repeat
from threading import Thread
from Queue import Queue, Empty
import gimp

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
        if self.pas is not None:
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
        self.stopping = False

    def start_stop_tx(self):
        if self.tx_enabled.get():
            self.stopping = False
            self.audio_thread = AudioThread(self.sstv, self)
            self.audio_thread.start()
        else:
            self.stop()
            if self.progress is not None:
                self.progress.update_image()

    def stop(self):
        if self.audio_thread is not None:
            self.stopping = True
            self.audio_thread.stop()

    def audio_thread_ended(self):
        if not self.stopping:
            self.tx_enabled.set(0)

    def close(self):
        self.root.destroy()


class CanvasUpdater(Thread):
    def __init__(self, progress):
        Thread.__init__(self)
        self.progress = progress
        self.queue = Queue()
        self.should_run = True

    def stop(self):
        self.should_run = False

    def update_image(self, line=None):
        self.queue.put(line)

    def run(self):
        while self.should_run:
            try:
                self.progress.update_image(self.queue.get(timeout=0.5))
            except Empty:
                pass


class ProgressCanvas(Canvas):
    def __init__(self, master, image):
        self.height_ratio = 1
        width, height = image.size
        pixels = image.load()
        RED, GREEN, BLUE = range(3)
        self.colors = ['#{0:02x}{1:02x}{2:02x}'.format(
            contrast(sum(pixels[x, y][RED]   for x in xrange(width)) / width),
            contrast(sum(pixels[x, y][GREEN] for x in xrange(width)) / width),
            contrast(sum(pixels[x, y][BLUE]  for x in xrange(width)) / width))
            for y in xrange(height)]
        if height / float(width) > 1.5:
            width *= 2
        elif width < 200:
            width *= 2
            height *= 2
            self.height_ratio = 2
        if (width, height) != image.size:
            image = image.resize((width, height))
        Canvas.__init__(self, master, width=width, height=height)
        self.tk_img = ImageTk.PhotoImage(image)
        self.update_image()
        self.pack()

    def update_image(self, line=None):
        image = self.tk_img
        self.create_image(0, 0, anchor=NW, image=image)
        if line is not None:
            fill = self.colors[line]
            line *= self.height_ratio
            self.create_line(0, line, image.width(), line, fill=fill)


def contrast(value):
    if 80 < value < 160:
        return value + (80 if value < 120 else -80)
    else:
        return 255 - value

def transmit_current_image(image, drawable, mode, vox, fskid):
    sstv = MODULE_MAP[mode]
    pil_img = match_image_with_sstv_mode(image_gimp_to_pil(image), sstv)
    root = Tk()
    cu = CanvasUpdater(ProgressCanvas(root, pil_img))
    cu.start()
    tm = Transmitter(init_sstv(sstv, pil_img, vox, fskid), root, cu)
    tm1750 = Transmitter(Sine1750(None, 44100, 16), None, None)
    buttons = Frame(root)
    for text, tram in (('TX', tm), ('1750 Hz', tm1750)):
        Checkbutton(buttons, text=text, indicatoron=False, padx=5, pady=5,
                variable=tram.tx_enabled, command=tram.start_stop_tx).pack(side=LEFT)
    Button(buttons, text="Close", command=tm.close).pack(side=LEFT)
    buttons.pack()
    root.mainloop()
    for obj in (tm, tm1750, cu):
        obj.stop()

def image_gimp_to_pil(image):
    try:
        sandbox = image.duplicate()
        for layer in sandbox.layers:
            if not layer.visible:
                sandbox.remove_layer(layer)
        sandbox.merge_visible_layers(CLIP_TO_IMAGE)
        layer = sandbox.layers[0]
        if not layer.is_rgb:
            pdb.gimp_image_convert_rgb(sandbox)
        if layer.has_alpha:
            pdb.gimp_layer_flatten(layer)
        w, h = layer.width, layer.height
        pixels = layer.get_pixel_rgn(0, 0, w, h)[:, :] # all pixels
        return Image.frombuffer('RGB', (w, h), pixels, 'raw', 'RGB', 0, 0)
    finally:
        gimp.delete(sandbox)

def match_image_with_sstv_mode(image, mode):
    mode_size = mode.WIDTH, mode.HEIGHT
    if image.size != mode_size:
        image = image.resize(mode_size, Image.ANTIALIAS)
    if 'grayscale' in mode.__module__:
        image = image.convert('LA').convert('RGB')
    return image

def init_sstv(mode, image, vox, fskid):
    s = mode(image, 44100, 16)
    s.vox_enabled = vox
    if fskid:
        s.add_fskid_text(fskid)
    return s

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
