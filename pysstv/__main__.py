#!/usr/bin/env python

from __future__ import print_function, division
from PIL import Image
from argparse import ArgumentParser
from sys import stderr
from pysstv import color, grayscale

SSTV_MODULES = [color, grayscale]


def main():
    module_map = build_module_map()
    parser = ArgumentParser(
        description='Converts an image to an SSTV modulated WAV file.')
    parser.add_argument('img_file', metavar='image.png',
                        help='input image file name')
    parser.add_argument('wav_file', metavar='output.wav',
                        help='output WAV file name')
    parser.add_argument(
        '--mode', dest='mode', default='MartinM1', choices=module_map,
        help='image mode (default: Martin M1)')
    parser.add_argument('--rate', dest='rate', type=int, default=48000,
                        help='sampling rate (default: 48000)')
    parser.add_argument('--bits', dest='bits', type=int, default=16,
                        help='bits per sample (default: 16)')
    parser.add_argument('--vox', dest='vox', action='store_true',
                        help='add VOX tones at the beginning')
    parser.add_argument('--fskid', dest='fskid',
                        help='add FSKID at the end')
    parser.add_argument('--chan', dest='chan', type=int,
                        help='number of channels (default: mono)')
    parser.add_argument('--resize', dest='resize', action='store_true',
                        help='resize the image to the correct size')
    parser.add_argument('--keep-aspect-ratio', dest='keep_aspect_ratio', action='store_true',
                        help='keep the original aspect ratio when resizing (and cut off excess pixels)')
    parser.add_argument('--resample', dest='resample', default='lanczos',
                        choices=('nearest', 'bicubic', 'lanczos'),
                        help='which resampling filter to use for resizing (see Pillow documentation)')
    args = parser.parse_args()
    image = Image.open(args.img_file)
    mode = module_map[args.mode]
    if args.resize and any(i != m for i, m in zip(image.size, (mode.WIDTH, mode.HEIGHT))):
        resample = getattr(Image, args.resample.upper())
        if args.keep_aspect_ratio:
            orig_ratio = image.width / image.height
            mode_ratio = mode.WIDTH / mode.HEIGHT
            crop = orig_ratio != mode_ratio
        else:
            crop = False
        if crop:
            if orig_ratio < mode_ratio:
                w = mode.WIDTH
                h = int(w / orig_ratio)
            else:
                h = mode.HEIGHT
                w = int(orig_ratio * h)
        else:
            w = mode.WIDTH
            h = mode.HEIGHT
        image = image.resize((w, h), resample)
        if crop:
            x = (image.width - mode.WIDTH) / 2
            y = (image.height - mode.HEIGHT) / 2
            image = image.crop((x, y, mode.WIDTH + x, mode.HEIGHT + y))
    elif not all(i >= m for i, m in zip(image.size, (mode.WIDTH, mode.HEIGHT))):
        print(('Image must be at least {m.WIDTH} x {m.HEIGHT} pixels '
               'for mode {m.__name__}').format(m=mode), file=stderr)
        raise SystemExit(1)
    s = mode(image, args.rate, args.bits)
    s.vox_enabled = args.vox
    if args.fskid:
        s.add_fskid_text(args.fskid)
    if args.chan:
        s.nchannels = args.chan
    s.write_wav(args.wav_file)


def build_module_map():
    try:
        from collections import OrderedDict
        module_map = OrderedDict()
    except ImportError:
        module_map = {}
    for module in SSTV_MODULES:
        for mode in module.MODES:
            module_map[mode.__name__] = mode
    return module_map


if __name__ == '__main__':
    main()
