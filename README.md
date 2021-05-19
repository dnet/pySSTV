SSTV generator in pure Python
=============================

[![Build Status](https://travis-ci.org/dnet/pySSTV.svg?branch=master)](https://travis-ci.org/dnet/pySSTV)

PySSTV generates SSTV modulated WAV files from any image that PIL can open
(PNG, JPEG, GIF, and many others). These WAV files then can be played by any
audio player connected to a shortwave radio for example.

My main motivation was to understand the internals of SSTV in practice, so
performance is far from optimal. I tried keeping the code readable, and only
performed such optimizations that wouldn't have complicated the codebase.

Command line usage
------------------

    $ python -m pysstv -h
    usage: __main__.py [-h]
                  [--mode {MartinM1,MartinM2,ScottieS1,ScottieS2,Robot36,PasokonP3,PasokonP5,PasokonP7,PD90,PD120,PD160,PD180,PD240,PD290,Robot8BW,Robot24BW}]
                  [--rate RATE] [--bits BITS] [--vox] [--fskid FSKID]
                  [--chan CHAN]
                  image.png output.wav

    Converts an image to an SSTV modulated WAV file.

    positional arguments:
      image.png             input image file name
      output.wav            output WAV file name

    optional arguments:
      -h, --help            show this help message and exit
      --mode {MartinM1,MartinM2,ScottieS1,ScottieS2,Robot36,PasokonP3,PasokonP5,PasokonP7,PD90,PD120D160,PD180,PD240,Robot8BW,Robot24BW}
                            image mode (default: Martin M1)
      --rate RATE           sampling rate (default: 48000)
      --bits BITS           bits per sample (default: 16)
      --vox                 add VOX tones at the beginning
      --fskid FSKID         add FSKID at the end
      --chan CHAN           number of channels (default: mono)

Python interface
----------------

The `SSTV` class in the `sstv` module implements basic SSTV-related
functionality, and the classes of other modules such as `grayscale` and
`color` extend this. Most instances implement the following methods:

 - `__init__` takes a PIL image, the samples per second, and the bits per
   sample as a parameter, but doesn't perform any hard calculations
 - `gen_freq_bits` generates tuples that describe a sine wave segment with
   frequency in Hz and duration in ms
 - `gen_values` generates samples between -1 and +1, performing sampling
   according to the samples per second value given during construction
 - `gen_samples` generates discrete samples, performing quantization
   according to the bits per sample value given during construction
 - `write_wav` writes the whole image to a Microsoft WAV file

The above methods all build upon those above them, for example `write_wav`
calls `gen_samples`, while latter calls `gen_values`, so typically, only
the first and the last, maybe the last two should be called directly, the
others are just listed here for the sake of completeness and to make the
flow easier to understand.

License
-------

The whole project is available under MIT license.

Useful links
------------

 - receive-only "counterpart": https://github.com/windytan/slowrx
 - free SSTV handbook: http://www.sstv-handbook.com/
 - robot 36 encoder/decoder in C: https://github.com/xdsopl/robot36/

Dependencies
------------

 - Python 3.5 or later
 - Python Imaging Library (Debian/Ubuntu package: `python-imaging`)
