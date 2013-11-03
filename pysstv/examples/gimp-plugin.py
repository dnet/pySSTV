#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# copy to ~/.gimp-2.8/plug-ins/
# dependencies: GIMP 2.8, python-imaging-tk

from gimpfu import register, main, pdb, PF_BOOL, PF_STRING, PF_RADIO
from tempfile import mkstemp
from PIL import Image, ImageTk
from Tkinter import Tk, Label
from pysstv import __main__ as pysstv_main
import os

MODULE_MAP = pysstv_main.build_module_map()

def transmit_current_image(image, drawable, mode, vox, fskid):
    handle, png_fn = mkstemp(suffix='.png', prefix='pysstv-gimp-')
    os.fdopen(handle).close()
    try:
        pdb.gimp_file_save(image, drawable, png_fn, png_fn)
        pil_img = Image.open(png_fn)
        root = Tk()
        tk_img = ImageTk.PhotoImage(pil_img)
        img_widget = Label(root, image=tk_img)
        img_widget.image = tk_img
        img_widget.pack()
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
