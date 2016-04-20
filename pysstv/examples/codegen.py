#!/usr/bin/env python

class Image(object):
    def __init__(self, content):
        self.content = content

    def load(self):
        return self

    def __getitem__(self, item):
        if isinstance(item, tuple):
            x, y = item
            return Image('{0}[(ROW({1}) + COL({2})) * 3'.format(self.content, y, x))
        elif isinstance(item, int):
            return Image('{0} + RGB({1})]'.format(self.content, item))
        else:
            raise NotImplementedError()

    def __rmul__(self, n):
        return Image('({1} * {0})'.format(self.content, float(n)))

    def __mul__(self, n):
        return Image('({0} * {1})'.format(self.content, float(n)))

    def __rtruediv__(self, n):
        return Image('({1} / {0})'.format(self.content, n))

    def __truediv__(self, n):
        return Image('({0} / {1})'.format(self.content, n))

    def __radd__(self, n):
        return Image('({1} + {0})'.format(self.content, n))

    def __add__(self, n):
        return Image('({0} + {1})'.format(self.content, n))

    def __str__(self):
        return self.content

from pysstv.color import MartinM1, MartinM2, PasokonP3, PasokonP5, PasokonP7
import re

supported = [MartinM1, MartinM2, PasokonP3, PasokonP5, PasokonP7]
ROW_RE = re.compile(r'ROW\(\d+\)')

def main(sstv_class=None):
    if sstv_class is None:
        sstv_class = MartinM1
    elif sstv_class not in supported:
        raise NotImplementedError()
    sstv = sstv_class(Image('img'), 44100, 16)
    n = 0
    yield '#define ROW(x) x'
    yield '#define COL(x) x'
    yield '#define RGB(x) x'
    yield 'void convert(unsigned char *img, float *freqs, float *msecs, const int width) {\nint frq = 0;'
    history = []
    lut = {}
    same_as = {}
    for freq, msec in sstv.gen_freq_bits():
        printed = 'freqs[frq] = {1}; msecs[frq++] = {2};'.format(n, freq, msec)
        key = ROW_RE.sub('row', printed)
        old = lut.get(key)
        if old is not None:
            same_as[n] = old
        else:
            lut[key] = n
        history.append((printed, key))
        n += 1
    del lut
    m_start, m_len = gen_matches(same_as, history, n)
    for i in xrange(same_as[m_start]):
        yield history[i][0]
    yield 'for (int row = 0; row < width * {0}; row += width) {{'.format(sstv.HEIGHT)
    for i in xrange(same_as[m_start], same_as[m_start] + m_len - 1):
        yield ' ' + history[i][1]
    yield '}'
    yield '}}\n\n#define FREQ_COUNT {0}'.format(n)



def gen_matches(same_as, history, n):
    cur_start = None
    cur_len = None
    cur_end = None
    for i in xrange(n):
        if cur_start is None:
            tmp = same_as.get(i)
            if tmp is not None:
                cur_len = 1
                cur_start = i
                cur_end = tmp
        else:
            tmp = same_as.get(i)
            if tmp is not None and history[tmp][1] == history[cur_end + 1][1] and cur_start > cur_end:
                cur_len += 1
                cur_end += 1
            else:
                if tmp is not None and history[tmp][1] == history[cur_end + 1][1]:
                    return cur_start, cur_len
                tmp = same_as.get(i)
                if tmp is None:
                    cur_start = None
                else:
                    cur_len = 1
                    cur_start = i
                    cur_end = tmp

def test(img_file):
    from subprocess import Popen, PIPE, check_output
    from os import remove, path
    from PIL import Image
    from datetime import datetime
    import struct
    exe = './codegen-test-executable'
    if not path.exists('stb_image.h'):
        from urllib import urlretrieve
        urlretrieve('https://raw.githubusercontent.com/nothings/stb/master/stb_image.h', 'stb_image.h')
    try:
        for sstv_class in supported:
            print 'Testing', sstv_class
            gcc = Popen(['gcc', '-xc', '-lm', '-o', exe, '-'], stdin=PIPE)
            start = datetime.now()
            with open(path.join(path.dirname(__file__), 'codeman.c')) as cm:
                c_src = cm.read().replace('#include "codegen.c"', '\n'.join(main(sstv_class)))
                gcc.communicate(c_src)
            gen_elapsed = datetime.now() - start
            print ' - gengcc took', gen_elapsed
            start = datetime.now()
            gen = check_output([exe, img_file])
            native_elapsed = datetime.now() - start
            print ' - native took', native_elapsed
            img = Image.open(img_file)
            sstv = sstv_class(img, 44100, 16)
            start = datetime.now()
            try:
                for n, (freq, msec) in enumerate(sstv.gen_freq_bits()):
                    assert gen[n * 8:(n + 1) * 8] == struct.pack('ff', freq, msec)
            except AssertionError:
                mode_name = sstv_class.__name__
                with file('/tmp/{0}-c.bin'.format(mode_name), 'wb') as f:
                    f.write(gen)
                with file('/tmp/{0}-py.bin'.format(mode_name), 'wb') as f:
                    for n, (freq, msec) in enumerate(sstv.gen_freq_bits()):
                        f.write(struct.pack('ff', freq, msec))
                with file('/tmp/{0}.c'.format(mode_name), 'w') as f:
                    f.write(c_src)
                print (" ! Outputs are different, they've been saved to "
                    "/tmp/{0}-{{c,py}}.bin, along with the C source code "
                    "in /tmp/{0}.c").format(mode_name)
            python_elapsed = datetime.now() - start
            print ' - python took', python_elapsed
            print ' - speedup:', python_elapsed.total_seconds() / native_elapsed.total_seconds()
        print 'OK'
    finally:
        try:
            remove(exe)
        except OSError:
            pass


if __name__ == '__main__':
    from sys import argv
    if len(argv) > 2 and argv[1] == 'test':
        test(argv[2])
    else:
        print '\n'.join(main())
