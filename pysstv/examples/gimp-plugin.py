#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# copy to ~/.gimp-2.8/plug-ins/
# dependencies: GIMP 2.8, python-imaging-tk

from gimpfu import register, main, pdb, PF_BOOL, PF_STRING, PF_RADIO
from tempfile import mkstemp
from PIL import Image, ImageTk
from Tkinter import Tk, Label, Button, Checkbutton, IntVar
from pysstv import __main__ as pysstv_main
from pysstv.examples.pyaudio_sstv import PyAudioSSTV
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


class Transmitter(object):
    def __init__(self, sstv, root):
        def encode_line_hooked(line):
            print line # TODO show progress on GUI
            return self.original_encode_line(line)
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

    def audio_thread_ended(self):
        self.tx_enabled.set(0)

    def close(self, e):
        self.root.destroy()


def transmit_current_image(image, drawable, mode, vox, fskid):
    sstv = MODULE_MAP[mode]
    handle, png_fn = mkstemp(suffix='.png', prefix='pysstv-gimp-')
    os.fdopen(handle).close()
    try:
        pdb.gimp_file_save(image, drawable, png_fn, png_fn)
        pil_img = Image.open(png_fn)
        root = Tk()
        s = sstv(pil_img, 44100, 16)
        s.vox_enabled = vox
        if fskid:
            s.add_fskid_text(fskid)
        tm = Transmitter(s, root)
        tk_img = ImageTk.PhotoImage(pil_img)
        img_widget = Label(root, image=tk_img)
        img_widget.image = tk_img
        img_widget.pack()
        start_btn = Checkbutton(root, text="TX", indicatoron=False, padx=5,
                pady=5, variable=tm.tx_enabled, command=tm.start_stop_tx)
        start_btn.pack()
        close_btn = Button(root, text="Close")
        close_btn.bind('<Button-1>', tm.close)
        close_btn.pack()
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
