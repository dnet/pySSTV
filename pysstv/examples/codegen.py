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
            raise NotImplemented

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
    mgen = iter(gen_matches(same_as, history, n))
    m_start, m_len, m_end = next(mgen)
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
    matches = []
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
                    yield cur_start, cur_len, cur_end
                tmp = same_as.get(i)
                if tmp is None:
                    cur_start = None
                else:
                    cur_len = 1
                    cur_start = i
                    cur_end = tmp


if __name__ == '__main__':
    main()
