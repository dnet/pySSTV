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

from pysstv.color import MartinM1
import re

supported = [MartinM1]
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
    yield '#define RGB(x) (2 - (x))'
    yield 'void convert(unsigned char *img, float *freqs, float *msecs) {\nint frq = 0;'
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
    yield 'for (int row = {0}; row >= 0; row -= {1}) {{'.format(
            (sstv.HEIGHT - 1) * sstv.WIDTH, sstv.WIDTH)
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

def test():
    from subprocess import Popen, PIPE, check_output
    from os import remove, path
    from PIL import Image
    from datetime import datetime
    import struct
    exe = './codegen-test-executable'
    try:
        for sstv_class in supported:
            print 'Testing', sstv_class
            gcc = Popen(['gcc', '-xc', '-o', exe, '-'], stdin=PIPE)
            start = datetime.now()
            with open(path.join(path.dirname(__file__), 'codeman.c')) as cm:
                gcc.communicate(cm.read().replace('#include "codegen.c"', '\n'.join(main(sstv_class))))
            gen_elapsed = datetime.now() - start
            print ' - gengcc took', gen_elapsed
            start = datetime.now()
            gen = check_output([exe])
            native_elapsed = datetime.now() - start
            print ' - native took', native_elapsed
            img = Image.open("320x256rgb.png")
            sstv = sstv_class(img, 44100, 16)
            start = datetime.now()
            for n, (freq, msec) in enumerate(sstv.gen_freq_bits()):
                assert gen[n * 8:(n + 1) * 8] == struct.pack('ff', freq, msec)
            python_elapsed = datetime.now() - start
            print ' - python took', python_elapsed
            print ' - speedup:', python_elapsed.total_seconds() / native_elapsed.total_seconds()
        print 'OK'
    finally:
        remove(exe)


if __name__ == '__main__':
    from sys import argv
    if len(argv) > 1 and argv[1] == 'test':
        test()
    else:
        print '\n'.join(main())
