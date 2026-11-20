# bigpig-news v3 — Friday 20 November 2026, one image.
# Pure Python 3.13 standard library only (math, os, struct, zlib).
# No PIL, no network. Two runs write byte-identical PNGs.
# Written fresh for the v3 rebuild: stroke-serif typography, consensus
# Friday slate (Kyiv barrage / Akvan / COP31), recognizable world map.

import math
import os
import struct
import zlib

W, H = 1024, 1024

CREAM = (247, 242, 230)
PAPER = (250, 246, 236)
INK = (26, 26, 26)
RED = (160, 30, 34)
DARKRED = (122, 20, 24)
NAVY = (18, 42, 68)
SKY = (58, 110, 158)
TEAL = (18, 110, 110)
GOLD = (198, 142, 32)
GREY = (110, 105, 95)
LIGHT = (232, 226, 210)
RULE = (26, 26, 26)

BLUE_CHIP = (28, 84, 150)
GREEN_CHIP = (32, 120, 72)
RED_CHIP = (178, 42, 38)
BROWN_CHIP = (146, 96, 44)
PURPLE_CHIP = (110, 72, 150)
TEAL_CHIP = (16, 120, 118)
GREY_CHIP = (96, 96, 96)


class Sheet:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.buf), 3):
            self.buf[i] = r
            self.buf[i + 1] = g
            self.buf[i + 2] = b

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def rect(self, x, y, w, h, c):
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.w, int(x + w))
        y1 = min(self.h, int(y + h))
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x0, x1, y, c):
        if y < 0 or y >= self.h:
            return
        a = max(0, int(x0))
        b = min(self.w - 1, int(x1))
        for xx in range(a, b + 1):
            i = (y * self.w + xx) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def line(self, x0, y0, x1, y1, c):
        # Bresenham, 1px.
        x0 = int(round(x0))
        y0 = int(round(y0))
        x1 = int(round(x1))
        y1 = int(round(y1))
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick(self, x0, y0, x1, y1, w, c):
        # A segment drawn as a filled quad (fast, deterministic).
        w = max(1, int(round(w)))
        if w == 1:
            self.line(x0, y0, x1, y1, c)
            return
        dx = x1 - x0
        dy = y1 - y0
        ln = math.hypot(dx, dy)
        if ln < 0.001:
            self.disc(int(round(x0)), int(round(y0)), w // 2, c)
            return
        nx = -dy / ln * (w / 2.0)
        ny = dx / ln * (w / 2.0)
        self.poly([
            (x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
            (x1 - nx, y1 - ny), (x0 - nx, y0 - ny),
        ], c)

    def poly(self, pts, c):
        # Scanline fill of a polygon. Integer coords, deterministic.
        pts = [(int(round(x)), int(round(y))) for x, y in pts]
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, min(ys))
        y1 = min(self.h - 1, max(ys))
        n = len(pts)
        for y in range(y0, y1 + 1):
            xs = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if ay == by:
                    continue
                if (y >= min(ay, by)) and (y < max(ay, by)):
                    x = ax + (y - ay) * (bx - ax) / (by - ay)
                    xs.append(x)
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                a = max(0, int(math.ceil(xs[k])))
                b = min(self.w - 1, int(math.floor(xs[k + 1])))
                for xx in range(a, b + 1):
                    self.px(xx, y, c)

    def disc(self, cx, cy, r, c):
        cx = int(round(cx))
        cy = int(round(cy))
        r = int(round(r))
        if r <= 0:
            self.px(cx, cy, c)
            return
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def ring(self, cx, cy, r, w, c):
        for k in range(w):
            rr = r - k
            if rr <= 0:
                break
            steps = max(24, int(2 * math.pi * rr))
            for s in range(steps):
                a = 2 * math.pi * s / steps
                self.px(int(round(cx + rr * math.cos(a))),
                        int(round(cy + rr * math.sin(a))), c)

    def checker(self, x, y, w, h, c1, c2, s=4):
        # Deterministic 2-colour dither (newsprint halftone feel).
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.px(xx, yy, c1 if ((xx // s) + (yy // s)) % 2 == 0 else c2)

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)


def write_png(sheet, path):
    raw = bytearray()
    stride = sheet.w * 3
    for y in range(sheet.h):
        raw.append(0)
        raw += sheet.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", sheet.w, sheet.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- serif font
# Glyphs as strokes on a 7-wide x 13-tall grid: cap top y=0, x-height
# top y=4, baseline y=9, descender bottom y=12. Each glyph is a list of
# strokes; each stroke is a list of (x, y) points. Rendered with thick
# segments: verticals full width, horizontals thinner (serif contrast),
# plus explicit foot serifs baked into the strokes.

def _s(*pts):
    return [pts]

SERIF = {
    'A': [[(3, 0), (0, 9)], [(3, 0), (6, 9)], [(1, 6), (5, 6)]],
    'B': [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 4), (4, 5), (0, 5)],
          [(0, 5), (4, 5), (6, 7), (6, 8), (4, 9), (0, 9)]],
    'C': [[(6, 1), (4, 0), (2, 0), (0, 2), (0, 7), (2, 9), (4, 9), (6, 8)]],
    'D': [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 7), (4, 9), (0, 9)]],
    'E': [[(0, 0), (0, 9)], [(0, 0), (6, 0)], [(0, 4), (5, 4)], [(0, 9), (6, 9)],
          [(-1, 9), (1, 9)]],
    'F': [[(0, 0), (0, 9)], [(0, 0), (6, 0)], [(0, 4), (5, 4)], [(-1, 9), (1, 9)]],
    'G': [[(6, 1), (4, 0), (2, 0), (0, 2), (0, 7), (2, 9), (4, 9), (6, 8),
           (6, 5)], [(6, 5), (3, 5)]],
    'H': [[(0, 0), (0, 9)], [(6, 0), (6, 9)], [(0, 4), (6, 4)],
          [(-1, 9), (1, 9)], [(5, 9), (7, 9)]],
    'I': [[(3, 0), (3, 9)], [(1, 0), (5, 0)], [(1, 9), (5, 9)]],
    'J': [[(1, 0), (6, 0)], [(5, 0), (5, 8), (4, 9), (2, 9), (1, 8)]],
    'K': [[(0, 0), (0, 9)], [(5, 0), (2, 5)], [(2, 5), (6, 9)],
          [(-1, 9), (1, 9)]],
    'L': [[(0, 0), (0, 9)], [(0, 9), (6, 9)], [(-1, 9), (1, 9)]],
    'M': [[(0, 9), (0, 0)], [(0, 0), (3, 5)], [(3, 5), (6, 0)], [(6, 0), (6, 9)],
          [(-1, 9), (1, 9)], [(5, 9), (7, 9)]],
    'N': [[(0, 9), (0, 0)], [(0, 0), (6, 9)], [(6, 0), (6, 9)],
          [(-1, 9), (1, 9)], [(5, 9), (7, 9)]],
    'O': [[(2, 0), (4, 0), (6, 2), (6, 7), (4, 9), (2, 9), (0, 7), (0, 2), (2, 0)]],
    'P': [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 4), (4, 5), (0, 5)],
          [(-1, 9), (1, 9)]],
    'Q': [[(2, 0), (4, 0), (6, 2), (6, 7), (4, 9), (2, 9), (0, 7), (0, 2), (2, 0)],
          [(4, 6), (6, 9)]],
    'R': [[(0, 0), (0, 9)], [(0, 0), (4, 0), (6, 2), (6, 4), (4, 5), (0, 5)],
          [(3, 5), (6, 9)], [(-1, 9), (1, 9)]],
    'S': [[(6, 1), (4, 0), (2, 0), (0, 2), (0, 3), (2, 4), (4, 4), (6, 5),
           (6, 7), (4, 9), (2, 9), (0, 8)]],
    'T': [[(0, 0), (6, 0)], [(3, 0), (3, 9)], [(1, 9), (5, 9)]],
    'U': [[(0, 0), (0, 7), (2, 9), (4, 9), (6, 7), (6, 0)]],
    'V': [[(0, 0), (3, 9)], [(6, 0), (3, 9)]],
    'W': [[(0, 0), (1, 9)], [(1, 9), (3, 4)], [(3, 4), (5, 9)], [(5, 9), (6, 0)]],
    'X': [[(0, 0), (6, 9)], [(6, 0), (0, 9)]],
    'Y': [[(0, 0), (3, 5)], [(6, 0), (3, 5)], [(3, 5), (3, 9)], [(1, 9), (5, 9)]],
    'Z': [[(0, 0), (6, 0)], [(6, 0), (0, 9)], [(0, 9), (6, 9)]],
    'a': [[(1, 6), (2, 4), (4, 4), (6, 6), (6, 8), (5, 9), (2, 9), (0, 7), (1, 6)],
          [(6, 4), (6, 9)]],
    'b': [[(0, 0), (0, 9)], [(0, 6), (3, 4), (5, 5), (6, 7), (4, 9), (0, 9)],
          [(-1, 9), (1, 9)]],
    'c': [[(6, 5), (4, 4), (2, 4), (0, 6), (0, 8), (2, 9), (4, 9), (6, 8)]],
    'd': [[(0, 6), (2, 4), (4, 4), (6, 6), (6, 8), (4, 9), (2, 9), (0, 7)],
          [(6, 0), (6, 9)]],
    'e': [[(0, 7), (1, 5), (3, 4), (5, 5), (6, 7), (5, 9), (2, 9), (0, 7)],
          [(0, 6), (6, 6)]],
    'f': [[(1, 1), (3, 0), (4, 1)], [(3, 1), (3, 9)], [(1, 5), (5, 5)]],
    'g': [[(1, 6), (3, 4), (5, 5), (6, 7), (4, 9), (1, 9), (0, 7)],
          [(6, 4), (6, 10), (4, 12), (1, 12)]],
    'h': [[(0, 0), (0, 9)], [(0, 5), (2, 4), (4, 4), (6, 6), (6, 9)],
          [(-1, 9), (1, 9)]],
    'i': [[(1, 4), (1, 9)], [(1, 1), (1, 2)], [(0, 9), (2, 9)]],
    'j': [[(2, 4), (2, 11), (0, 12)], [(2, 1), (2, 2)]],
    'k': [[(0, 0), (0, 9)], [(5, 4), (2, 7)], [(2, 7), (6, 9)],
          [(-1, 9), (1, 9)]],
    'l': [[(1, 0), (1, 9)], [(0, 9), (2, 9)]],
    'm': [[(0, 4), (0, 9)], [(0, 5), (1, 4), (3, 5), (3, 9)],
          [(3, 5), (4, 4), (6, 5), (6, 9)]],
    'n': [[(0, 4), (0, 9)], [(0, 5), (2, 4), (4, 4), (6, 6), (6, 9)]],
    'o': [[(2, 4), (4, 4), (6, 6), (6, 8), (4, 9), (2, 9), (0, 7), (0, 6), (2, 4)]],
    'p': [[(0, 4), (0, 12)], [(0, 5), (3, 4), (5, 5), (6, 7), (4, 9), (0, 9)]],
    'q': [[(0, 5), (3, 4), (5, 5), (6, 7), (4, 9), (0, 9)], [(6, 4), (6, 12)]],
    'r': [[(0, 4), (0, 9)], [(0, 5), (1, 4), (3, 4), (4, 5), (4, 6)]],
    's': [[(5, 4), (3, 4), (1, 5), (0, 6)], [(0, 6), (2, 7), (4, 7), (5, 8)],
          [(5, 8), (4, 9), (2, 9), (0, 8)]],
    't': [[(1, 4), (2, 4)], [(2, 4), (2, 11)], [(2, 11), (0, 12)],
          [(0, 6), (4, 6)]],
    'u': [[(0, 4), (0, 8), (1, 9), (3, 9), (5, 8), (6, 7)], [(6, 4), (6, 9)]],
    'v': [[(0, 4), (3, 9)], [(6, 4), (3, 9)]],
    'w': [[(0, 4), (1, 9)], [(1, 9), (3, 5)], [(3, 5), (5, 9)], [(5, 9), (6, 4)]],
    'x': [[(0, 4), (6, 9)], [(6, 4), (0, 9)]],
    'y': [[(0, 4), (3, 8)], [(6, 4), (3, 8)], [(3, 8), (3, 12), (1, 12)]],
    'z': [[(0, 4), (6, 4)], [(6, 4), (0, 9)], [(0, 9), (6, 9)]],
    '0': [[(2, 0), (4, 0), (6, 2), (6, 7), (4, 9), (2, 9), (0, 7), (0, 2), (2, 0)]],
    '1': [[(1, 2), (3, 0)], [(3, 0), (3, 9)], [(2, 9), (4, 9)]],
    '2': [[(1, 1), (3, 0), (5, 1), (5, 3), (4, 5), (0, 9)], [(0, 9), (6, 9)]],
    '3': [[(0, 1), (2, 0), (4, 0), (6, 2), (6, 4), (4, 5), (6, 6), (6, 8),
           (4, 9), (2, 9), (0, 8)]],
    '4': [[(4, 0), (0, 6)], [(0, 6), (5, 6)], [(4, 0), (4, 9)]],
    '5': [[(0, 0), (6, 0)], [(0, 0), (0, 4)],
          [(0, 4), (4, 4), (6, 6), (6, 8), (4, 9), (2, 9), (0, 7)]],
    '6': [[(5, 0), (3, 0), (1, 2), (0, 4), (0, 7), (1, 9), (3, 9), (5, 8),
           (6, 6), (5, 4), (3, 4), (1, 5)]],
    '7': [[(0, 0), (6, 0)], [(6, 0), (2, 9)]],
    '8': [[(2, 0), (4, 0), (6, 2), (5, 4), (4, 4), (2, 4), (0, 2), (2, 0)],
          [(2, 4), (4, 4), (6, 6), (6, 8), (4, 9), (2, 9), (0, 7), (0, 6), (2, 4)]],
    '9': [[(1, 4), (3, 4), (5, 5), (6, 7), (4, 9), (2, 9), (0, 7), (0, 6), (1, 4)],
          [(6, 4), (6, 9)]],
    '.': [[(3, 8), (3, 9)]],
    ',': [[(3, 8), (3, 9)], [(3, 9), (2, 11)]],
    ':': [[(3, 3), (3, 4)], [(3, 8), (3, 9)]],
    ';': [[(3, 3), (3, 4)], [(3, 8), (3, 9)], [(3, 9), (2, 11)]],
    '!': [[(3, 0), (3, 7)], [(3, 8), (3, 9)]],
    '?': [[(1, 1), (3, 0), (5, 1), (5, 3), (4, 4), (3, 5), (3, 6)],
          [(3, 8), (3, 9)]],
    "'": [[(3, 0), (2, 2)]],
    '"': [[(2, 0), (1, 2)], [(5, 0), (4, 2)]],
    '(': [[(4, 0), (2, 2), (2, 7), (4, 9)]],
    ')': [[(2, 0), (4, 2), (4, 7), (2, 9)]],
    '-': [[(0, 6), (6, 6)]],
    '/': [[(1, 9), (5, 0)]],
    '%': [[(1, 9), (5, 0)],
          [(0, 1), (2, 1), (2, 3), (0, 3), (0, 1)],
          [(4, 6), (6, 6), (6, 8), (4, 8), (4, 6)]],
    '$': [[(5, 1), (3, 0), (1, 1), (0, 3), (1, 4), (3, 5), (5, 5), (6, 7),
           (5, 9), (3, 9), (1, 8)], [(3, -1), (3, 10)]],
    '+': [[(3, 3), (3, 9)], [(0, 6), (6, 6)]],
    '=': [[(0, 4), (6, 4)], [(0, 7), (6, 7)]],
    '·': [[(3, 4), (3, 5)]],
    '•': [[(2, 4), (4, 4), (4, 6), (2, 6), (2, 4)]],
    '~': [[(0, 6), (2, 5), (4, 6), (6, 5)]],
    '–': [[(0, 6), (6, 6)]],
    '—': [[(-1, 6), (7, 6)]],
    '£': [[(5, 1), (3, 0), (1, 1), (0, 3), (1, 4), (3, 5), (3, 9), (0, 9)],
          [(0, 6), (4, 6)]],
    '&': [[(5, 0), (3, 0), (1, 1), (0, 3), (2, 5), (5, 5), (6, 6), (5, 9),
           (3, 9), (1, 7), (5, 3)]],
    '*': [[(3, 1), (3, 8)], [(0, 4), (6, 4)], [(1, 2), (5, 7)], [(5, 2), (1, 7)]],
}

ADV = {}
for _ch in SERIF:
    ADV[_ch] = 7
for _ch in 'ijlftI.,;:!\'"()·|':
    ADV[_ch] = 4
for _ch in 'MWmw%':
    ADV[_ch] = 8
for _ch in 'aceosunvxzbdghkpqyJLSCTUVYZEFPRBDK':
    ADV[_ch] = 6
ADV['r'] = 5
ADV[' '] = 4
ADV['-'] = 5
ADV['–'] = 6
ADV['—'] = 8
ADV['~'] = 6
ADV['$'] = 7
ADV['i'] = 3
ADV['l'] = 3
ADV['j'] = 3
ADV['t'] = 3.5
ADV['r'] = 4


class Type:
    """Stroke-serif text renderer. cap = cap height in px."""

    def __init__(self, sheet):
        self.s = sheet

    def width(self, text, cap):
        sc = cap / 9.0
        total = 0.0
        for ch in text:
            total += ADV.get(ch, 7) * sc * 0.80 + sc * 0.55
        return total - sc * 0.55 if text else 0.0

    def draw(self, x, y, text, cap, c, italic=False):
        # (x, y) = top-left of cap-height box (y = cap top).
        sc = cap / 9.0
        wfull = max(1, int(round(sc * 1.55)))
        whor = max(1, int(round(sc * 0.9)))
        cx = float(x)
        for ch in text:
            if ch == ' ':
                cx += ADV[' '] * sc * 0.80 + sc * 0.55
                continue
            strokes = SERIF.get(ch)
            if strokes is None:
                cx += 7 * sc * 0.80 + sc * 0.55
                continue
            for stroke in strokes:
                for a, b in zip(stroke, stroke[1:]):
                    ax = cx + a[0] * sc * 0.80
                    ay = y + a[1] * sc
                    bx = cx + b[0] * sc * 0.80
                    by = y + b[1] * sc
                    if italic:
                        ax += (9 - a[1]) * sc * 0.22
                        bx += (9 - b[1]) * sc * 0.22
                    horiz = abs(b[1] - a[1]) <= abs(b[0] - a[0]) / 3.0
                    wdt = whor if horiz else wfull
                    self.s.thick(ax, ay, bx, by, wdt, c)
            cx += ADV.get(ch, 7) * sc * 0.80 + sc * 0.55
        return cx

    def wrap(self, text, cap, maxw):
        words = text.split(' ')
        lines = []
        cur = ''
        for wd in words:
            trial = (cur + ' ' + wd).strip()
            if self.width(trial, cap) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, text, cap, c, maxw, leading=None, italic=False):
        lh = leading if leading is not None else int(cap * 1.45)
        yy = y
        for ln in self.wrap(text, cap, maxw):
            self.draw(x, yy, ln, cap, c, italic=italic)
            yy += lh
        return yy

# ---------------------------------------------------------------- scenes
# Every scene is drawn fresh here, inside its own box, with fixed coords.

def _strip(s, x, y, w, h, left, right, c1, c2):
    s.rect(x, y + h - 16, w, 16, (10, 10, 10))
    t = Type(s)
    t.draw(x + 6, y + h - 14, left, 11, c1)
    rw = t.width(right, 11)
    t.draw(x + w - 6 - rw, y + h - 14, right, 11, c2)


def scene_kyiv(s, x, y, w, h):
    s.checker(x, y, w, h, (16, 34, 58), (20, 42, 70), 5)
    # skyline
    base = y + h - 16
    sky = (8, 16, 30)
    for bx, bw, bh in [(0, 34, 34), (30, 22, 52), (50, 30, 40), (78, 26, 60),
                       (102, 30, 44), (130, 24, 56), (152, 28, 38),
                       (178, 26, 50), (202, 30, 42), (230, 24, 58),
                       (252, 28, 36), (278, 30, 48)]:
        s.rect(x + bx, base - bh, bw, bh, sky)
    for wx in range(8, w - 8, 14):
        for wy in range(base - 56, base - 6, 12):
            if (wx * 7 + wy * 3) % 5 < 2:
                s.rect(x + wx, wy, 3, 4, (232, 182, 60))
    # missile trails: three arcs with dots
    for (sx, sy, ex, ey) in [(18, 12, 96, 44), (120, 6, 210, 52), (200, 14, 268, 40)]:
        for k in range(9):
            t = k / 8.0
            px = sx + (ex - sx) * t
            py = sy + (ey - sy) * t - 14 * math.sin(math.pi * t)
            s.disc(x + px, y + py, 2, (255, 190, 90))
        s.disc(x + ex, y + ey, 4, (255, 120, 40))
        s.disc(x + ex, y + ey, 8, (255, 80, 20))
    # explosion bursts
    for (ex, ey) in [(52, base - 30), (150, base - 44), (248, base - 26)]:
        s.disc(x + ex, y + ey, 7, (255, 150, 40))
        s.disc(x + ex, y + ey, 4, (255, 220, 120))
        for a in range(0, 360, 45):
            r = math.radians(a)
            s.thick(x + ex, y + ey, x + ex + 11 * math.cos(r),
                    y + ey + 11 * math.sin(r), 2, (255, 150, 40))
    _strip(s, x, y, w, h, "01:25 LOCAL - 7 WAVES", "~30 MISSILES",
           (240, 240, 240), (255, 190, 90))


def scene_akvan(s, x, y, w, h):
    s.checker(x, y, w, h, (52, 128, 158), (44, 116, 146), 5)
    # coastline: sand on the left, sea on the right
    s.poly([(x, y), (x + 58, y), (x + 44, y + 60), (x + 62, y + h),
            (x, y + h)], (232, 214, 170))
    s.poly([(x + 58, y), (x + 78, y + 30), (x + 66, y + 70), (x + 82, y + h),
            (x + 62, y + h), (x + 44, y + 60)], (214, 192, 146))
    # houses
    for hx, hy in [(10, 66), (28, 84), (36, 58), (14, 100), (40, 96)]:
        s.rect(x + hx, y + hy, 12, 9, (240, 236, 220))
        s.poly([(x + hx - 1, y + hy), (x + hx + 6, y + hy - 6),
                (x + hx + 13, y + hy)], (178, 42, 38))
    # cyclone spiral
    cx, cy = x + w - 78, y + 52
    s.disc(cx, cy, 34, (250, 248, 240))
    for r in (28, 21, 14, 7):
        s.ring(cx, cy, r, 3, (30, 90, 130))
    s.disc(cx, cy, 5, (178, 42, 38))
    s.disc(cx + 26, cy - 18, 3, (178, 42, 38))
    t = Type(s)
    t.draw(x + 118, y + 8, "BAY OF BENGAL", 10, (250, 248, 240))
    _strip(s, x, y, w, h, "LANDFALL - GUSTS 110 KM/H", "CYCLONE AKVAN",
           (240, 240, 240), (255, 210, 90))


def scene_cop31(s, x, y, w, h):
    s.checker(x, y, w, h, (238, 232, 214), (230, 224, 204), 5)
    # globe
    cx, cy = x + 64, y + 52
    s.disc(cx, cy, 38, (52, 110, 158))
    s.poly([(cx - 20, cy - 12), (cx - 4, cy - 22), (cx + 10, cy - 10),
            (cx + 2, cy + 4), (cx - 12, cy + 2)], (72, 160, 92))
    s.poly([(cx - 6, cy + 12), (cx + 8, cy + 8), (cx + 16, cy + 20),
            (cx + 2, cy + 28), (cx - 10, cy + 22)], (72, 160, 92))
    s.ring(cx, cy, 38, 2, (26, 26, 26))
    # thermometer
    tx = x + w - 62
    s.rect(tx, y + 12, 16, 62, (250, 250, 250))
    s.frame(tx, y + 12, 16, 62, INK, 2)
    s.rect(tx + 3, y + 30, 10, 44, (178, 42, 38))
    s.disc(tx + 8, y + 78, 11, (178, 42, 38))
    s.disc(tx + 8, y + 78, 6, (220, 70, 60))
    # badge
    bx = x + w - 168
    s.rect(bx, y + 10, 148, 40, DARKRED)
    t = Type(s)
    t.draw(bx + 10, y + 15, "ANTALYA - NOV 20", 11, (250, 240, 210))
    t.draw(bx + 10, y + 30, "COP31", 16, (255, 255, 255))
    t.draw(bx + 72, y + 31, "FINAL DAY", 10, (255, 210, 90))
    _strip(s, x, y, w, h, "UN CLIMATE SUMMIT", "$120BN FINANCE GAP",
           (26, 26, 26), (160, 30, 34))


def scene_selloff(s, x, y, w, h):
    s.rect(x, y, w, h, (14, 20, 28))
    n = 7
    pts = []
    for k in range(n):
        px = 8 + (w - 16) * k / (n - 1)
        py = 8 + 24 * (k / (n - 1)) + (4 if k % 2 else 0)
        pts.append((px, py))
    for a, b in zip(pts, pts[1:]):
        s.thick(x + a[0], y + a[1], x + b[0], y + b[1], 3, (220, 60, 50))
    for px, py in pts:
        s.disc(x + px, y + py, 2, (255, 120, 90))
    _strip(s, x, y, w, h, "ASIA", "-4.9%",
           (220, 220, 220), (255, 150, 110))


def scene_bepi(s, x, y, w, h):
    s.rect(x, y, w, h, (10, 14, 24))
    for sx, sy in [(14, 8), (44, 16), (90, 6), (130, 12), (160, 8)]:
        s.disc(x + sx, y + sy, 1, (240, 240, 220))
    mx, my = x + w - 26, y + 16
    s.disc(mx, my, 11, (196, 192, 178))
    s.disc(mx - 4, my - 3, 2, (168, 164, 150))
    s.disc(mx + 3, my + 4, 2, (168, 164, 150))
    for k in range(6):
        t = k / 5.0
        px = x + 12 + (mx - 14 - x - 12) * t
        py = y + h - 22 - 18 * t
        if k % 2 == 0:
            s.disc(px, py, 1, (255, 210, 90))
    t = Type(s)
    t.draw(x + 6, y + 6, "6BN MILES", 10, (255, 210, 90))
    _strip(s, x, y, w, h, "ESA / JAXA", "8 YEARS",
           (230, 230, 230), (255, 210, 90))


def scene_burnham(s, x, y, w, h):
    s.rect(x, y, w, h, (238, 232, 214))
    fw = (w - 20) // 2
    fx, fy = x + 6, y + 6
    s.rect(fx, fy, fw, 26, (28, 60, 140))
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        s.disc(fx + fw / 2 + (fw / 2 - 8) * math.cos(a),
               fy + 13 + 9 * math.sin(a), 1, (255, 210, 60))
    ux, uy = x + w - 6 - fw, y + 6
    s.rect(ux, uy, fw, 26, (28, 60, 140))
    s.rect(ux, uy + 11, fw, 4, (255, 255, 255))
    s.rect(ux + fw // 2 - 2, uy, 4, 26, (255, 255, 255))
    s.rect(ux, uy + 12, fw, 2, (178, 42, 38))
    s.rect(ux + fw // 2 - 1, uy, 2, 26, (178, 42, 38))
    _strip(s, x, y, w, h, "BRUSSELS", "RESET",
           (26, 26, 26), (160, 30, 34))


def scene_japan(s, x, y, w, h):
    s.rect(x, y, w, h, (238, 232, 214))
    vals = [1.8, 1.9, 2.0, 2.1, 2.2]
    bw = (w - 16) // 5 - 4
    base = y + h - 20
    for i, v in enumerate(vals):
        bh = int(v * 12)
        col = RED if i == len(vals) - 1 else (120, 120, 116)
        s.rect(x + 8 + i * (bw + 4), base - bh, bw, bh, col)
    t = Type(s)
    t.draw(x + 6, y + 6, "CORE CPI, OCT", 9, INK)
    _strip(s, x, y, w, h, "CPI 2.2%", "BOJ EYED",
           (26, 26, 26), (160, 30, 34))


def scene_china(s, x, y, w, h):
    s.rect(x, y, w, h, (238, 232, 214))
    t = Type(s)
    t.draw(x + 6, y + 4, "1-YEAR", 9, INK)
    t.draw(x + 6, y + 16, "3.00%", 17, INK)
    s.rect(x + 6, y + 36, 64, 6, (120, 120, 116))
    hw = w // 2
    t.draw(x + hw + 4, y + 4, "5-YEAR", 9, INK)
    t.draw(x + hw + 4, y + 16, "3.50%", 17, RED)
    s.rect(x + hw + 4, y + 36, 58, 6, RED)
    _strip(s, x, y, w, h, "PBOC", "18 MO",
           (26, 26, 26), (160, 30, 34))


def scene_phillips(s, x, y, w, h):
    s.rect(x, y, w, h, (46, 130, 62))
    s.rect(x, y + h - 30, w, 10, (200, 178, 120))
    s.poly([(x + w - 84, y + 8), (x + w - 66, y + 4), (x + w - 48, y + 28),
            (x + w - 62, y + 34)], (222, 196, 140))
    s.rect(x + w - 58, y + 28, 5, 16, (120, 84, 44))
    s.disc(x + w - 24, y + 18, 8, (178, 42, 38))
    s.disc(x + w - 24, y + 18, 3, (120, 20, 20))
    t = Type(s)
    t.draw(x + 6, y + 6, "118", 20, (255, 255, 255))
    t.draw(x + 6, y + 28, "RECORD", 10, (255, 220, 90))
    _strip(s, x, y, w, h, "WELLINGTON", "NZ 368",
           (240, 240, 240), (255, 220, 90))


def scene_bukele(s, x, y, w, h):
    s.rect(x, y, w, h, (238, 232, 214))
    bx = x + w // 2 - 34
    s.rect(bx, y + 12, 68, 26, (28, 84, 150))
    s.rect(bx, y + 12, 68, 6, (20, 60, 110))
    s.rect(bx + 22, y + 5, 24, 9, (250, 250, 250))
    s.frame(bx + 22, y + 5, 24, 9, INK, 1)
    s.disc(bx + 34, y + 28, 7, (255, 255, 255))
    s.thick(bx + 30, y + 28, bx + 33, y + 31, 2, RED)
    s.thick(bx + 33, y + 31, bx + 39, y + 24, 2, RED)
    t = Type(s)
    t.draw(x + 6, y + 6, "2027", 14, RED)
    _strip(s, x, y, w, h, "FEB 2027", "3RD TERM",
           (26, 26, 26), (160, 30, 34))


def scene_senegal(s, x, y, w, h):
    s.checker(x, y, w, h, (52, 110, 158), (44, 98, 146), 5)
    for wy in (y + h - 24, y + h - 16):
        for wx in range(x, x + w, 14):
            s.thick(wx, wy, wx + 7, wy - 4, 2, (200, 225, 240))
            s.thick(wx + 7, wy - 4, wx + 14, wy, 2, (200, 225, 240))
    bx = x + w // 2 - 34
    s.poly([(bx, y + 12), (bx + 68, y + 12), (bx + 58, y + 26),
            (bx + 10, y + 26)], (120, 84, 44))
    s.rect(bx + 6, y + 26, 56, 4, (90, 60, 30))
    t = Type(s)
    t.draw(x + 6, y + 6, "YENNE COAST", 10, (255, 255, 255))
    _strip(s, x, y, w, h, "MISSING", "4 DEAD",
           (240, 240, 240), (255, 150, 110))


def scene_cgil(s, x, y, w, h):
    s.rect(x, y, w, h, (238, 232, 214))
    sw = (w - 16) // 3
    s.rect(x + 8, y + 6, sw, 22, (32, 130, 72))
    s.rect(x + 8 + sw, y + 6, sw, 22, (250, 250, 250))
    s.frame(x + 8 + sw, y + 6, sw, 22, INK, 1)
    s.rect(x + 8 + 2 * sw, y + 6, sw, 22, (178, 42, 38))
    for k in range(4):
        px = x + 10 + k * ((w - 20) // 4)
        s.rect(px, y + 32, 22, 10, (255, 255, 255))
        s.frame(px, y + 32, 22, 10, INK, 1)
    t = Type(s)
    t.draw(x + 6, y + 44, "100 SQUARES", 11, RED)
    _strip(s, x, y, w, h, "ROME", "STRIKE",
           (26, 26, 26), (160, 30, 34))


def scene_anthropic(s, x, y, w, h):
    s.rect(x, y, w, h, (22, 52, 40))
    data = [(10, 18, 30, 22), (30, 22, 34, 26), (50, 26, 38, 30),
            (70, 30, 42, 34), (90, 34, 46, 38), (110, 38, 52, 42),
            (130, 42, 56, 46)]
    step = (w - 20) / 7.0
    for i, (ox, lo, hi, cl) in enumerate(data):
        px = 10 + i * step
        up = cl > lo
        col = (72, 190, 110) if up else (220, 70, 60)
        s.thick(x + px + 4, y + lo, x + px + 4, y + hi, 1, col)
        s.rect(int(x + px), y + min(lo, cl), 9, max(3, abs(cl - lo)), col)
    t = Type(s)
    t.draw(x + 6, y + 6, "$97.17", 16, (255, 210, 90))
    _strip(s, x, y, w, h, "NASDAQ", "+17%",
           (230, 230, 230), (255, 210, 90))


# ---------------------------------------------------------------- map
# Simplified continent polygons, hand-sketched in the map box's own
# coordinates (map box is 330 wide x 200 tall here).

NA = [(18, 38), (30, 28), (55, 18), (90, 14), (120, 18), (150, 28),
      (170, 40), (185, 55), (175, 75), (160, 95), (140, 120), (120, 115),
      (95, 135), (70, 160), (55, 150), (45, 120), (25, 80), (15, 55)]
SA = [(75, 175), (95, 165), (115, 170), (135, 190), (130, 230), (115, 260),
      (100, 245), (85, 210), (70, 190)]
AF = [(185, 130), (210, 120), (240, 125), (265, 140), (270, 165),
      (255, 200), (240, 225), (220, 215), (200, 180), (185, 155)]
EU = [(185, 60), (195, 45), (215, 35), (250, 30), (280, 35), (320, 45),
      (325, 70), (310, 95), (290, 110), (280, 130), (260, 150),
      (240, 140), (225, 120), (205, 115), (195, 100), (185, 85),
      (175, 70)]
AU = [(275, 210), (300, 205), (315, 220), (305, 240), (285, 240),
      (270, 225)]

PINS = {1: (232, 78), 2: (243, 128), 3: (212, 92), 4: (296, 100),
        6: (200, 62), 7: (305, 96), 8: (282, 92), 9: (318, 268),
        10: (55, 140), 11: (178, 158), 12: (208, 72), 13: (130, 85)}


def draw_map(s, x, y, w, h):
    s.rect(x, y, w, h, NAVY)
    t = Type(s)
    for poly in (NA, SA, AF, EU, AU):
        pts = [(x + px * w / 330.0, y + py * h / 300.0) for px, py in poly]
        s.poly(pts, (232, 214, 170))
    # islands: UK, Japan, Indonesia, Madagascar, NZ
    for ix, iy, ir in [(196, 52, 3), (308, 88, 3), (306, 98, 2),
                       (272, 148, 3), (256, 196, 2), (262, 200, 2),
                       (316, 262, 3), (322, 266, 2), (246, 206, 2)]:
        s.disc(x + ix * w / 330.0, y + iy * h / 300.0, ir, (232, 214, 170))
    for num, (px, py) in PINS.items():
        cx = x + px * w / 330.0
        cy = y + py * h / 300.0
        s.disc(cx, cy, 9, RED)
        s.ring(cx, cy, 9, 1, (255, 255, 255))
        label = str(num)
        lw = t.width(label, 9)
        t.draw(cx - lw / 2, cy - 5, label, 9, (255, 255, 255))
    # space badge for story 5
    s.rect(x + 8, y + h - 24, 108, 18, (10, 10, 10))
    t.draw(x + 12, y + h - 21, "5 - SPACE, MERCURY", 9, (255, 210, 90))


def also_item(s, t, x, y, num, place, text, w, cap=10.5):
    # "14 HORMUZ - text... (Source)" wrapped; number+place in red.
    prefix = "%d %s - " % (num, place)
    src = ""
    if "(" in text and text.rstrip().endswith(")"):
        cut = text.rfind("(")
        src = text[cut:]
        text = text[:cut].rstrip()
    words = text.split(' ')
    lines = []
    cur = prefix
    cur_red = True
    for wd in words:
        trial = (cur + ' ' + wd).strip()
        if t.width(trial, cap) <= w or not cur:
            cur = trial
        else:
            lines.append((cur, cur_red))
            cur = wd
            cur_red = False
    if cur:
        lines.append((cur, cur_red))
    if src:
        last, last_red = lines[-1]
        trial = last + ' ' + src
        if t.width(trial, cap) <= w:
            lines[-1] = (trial, last_red)
        else:
            lines.append((src, False))
    yy = y
    lh = int(cap * 1.35)
    for ln, red_first in lines:
        if red_first:
            # draw the red prefix, then the rest in ink
            pre = prefix
            pw = t.width(pre, cap)
            t.draw(x, yy, pre, cap, RED)
            rest = ln[len(pre):]
            if rest:
                t.draw(x + pw, yy, rest, cap, INK)
        else:
            t.draw(x, yy, ln, cap, INK)
        yy += lh
    return yy


# ---------------------------------------------------------------- page

LEADS = [
    ("01", "KYIV, UKRAINE - WAR", "Russia fires 30 ballistic missiles at Kyiv",
     "Seven waves hit energy sites; 3 killed, bridges hit, power cut. (Kyiv Post, Reuters)",
     scene_kyiv),
    ("02", "ODISHA, INDIA - CYCLONE", "Cyclone Akvan makes landfall in India",
     "Crosses near Gopalpur at noon; 300,000+ moved, winds to 110 km/h. (IMD, The Hindu)",
     scene_akvan),
    ("03", "ANTALYA, TURKIYE - CLIMATE", "COP31 deadlocked on final day",
     "Draft drops fossil-fuel phase-out; $120bn finance unresolved. (UN News, Reuters)",
     scene_cop31),
]

CARDS = [
    ("04", "SEOUL / TOKYO - MARKETS", "AI sell-off sinks Asia to worst week",
     "Chipmakers led the slide; SoftBank -16%. (Reuters)", scene_selloff),
    ("05", "MERCURY - SPACE", "BepiColombo reaches Mercury after 8 years",
     "Probe ends 6bn-mile trip; orbit due Saturday. (ESA, BBC)", scene_bepi),
    ("06", "BRUSSELS - EUROPE", "Burnham holds first EU-UK reset summit",
     "Costa & von der Leyen host UK PM. (EU Council)", scene_burnham),
    ("07", "TOKYO - ECONOMY", "Japan inflation hits 2.2%; BoJ hike eyed",
     "Core CPI rises from 2.1%; above 2% for second month. (Reuters)", scene_japan),
    ("08", "BEIJING - RATES", "China holds lending rates for 18th month",
     "LPR stays at 3.0% and 3.5% as expected. (PBOC)", scene_china),
    ("09", "WELLINGTON - CRICKET", "Phillips makes history with 118 vs India",
     "First NZ batter with centuries in all formats. (ICC, AP)", scene_phillips),
    ("10", "SAN SALVADOR - POLITICS", "Bukele registers for third-term bid",
     "Files with electoral tribunal for Feb 2027 vote. (AP)", scene_bukele),
    ("11", "SENEGAL - MIGRATION", "Migrant boat capsizes off Yenne; 4 dead",
     "Dozens missing; Canary arrivals surge. (Al Jazeera)", scene_senegal),
    ("12", "ROME - LABOUR", "Italy's CGIL holds 24-hr general strike",
     "Unions rally in ~100 squares against 2027 budget. (CGIL, AFP)", scene_cgil),
    ("13", "NEW YORK - MARKETS", "Anthropic ends first day up 17%",
     "Claude maker closes at $97.17, up 17% on $83 offer. (Nasdaq)", scene_anthropic),
]

ALSO = [
    (14, "HORMUZ", "Four attacks on ships in 96 hours. (UKMTO)"),
    (15, "CINCINNATI", "Hippo Fiona dies after swallowing a hat. (AP)"),
    (16, "GAZA", "Aid groups rate peace plan 4 out of 26. (UN)"),
    (17, "LONDON", "UK & Norway fund 100m+ for naval vessels. (BBC)"),
    (18, "LOS ANGELES", "Thomas Markle ruled fit to stand trial. (BBC)"),
    (19, "JAKARTA", "Parliament passes asset-forfeiture bill. (Reuters)"),
    (20, "DUBLIN", "Harris seeks border-poll talks. (RTE)"),
    (21, "WASHINGTON", "US files emergency court bid on TPS. (AP)"),
    (22, "TAIPEI", "Taiwan tracks two Russian bombers. (Reuters)"),
    (23, "TURIN", "Alcaraz & Medvedev close ATP Finals. (ATP)"),
    (24, "NEW DELHI", "Pakistan minister to lead SCO delegation. (Hindu)"),
    (25, "SEOUL", "Ruling party moves to impeach chief justice. (SBS)"),
    (26, "BEIJING", "Loan prime rates held at 3.0%, 3.5%. (Xinhua)"),
    (27, "HONG KONG", "Hang Seng ~20% off January peak. (AP)"),
    (28, "SYDNEY", "ASX futures fall 1%; jobless rate 4.9%. (ABC)"),
    (29, "MUMBAI", "Sensex slips; Nifty stands at 25,199. (Reuters)"),
    (30, "TONGA", "Drought emergency as El Nino bites. (RNZ)"),
    (31, "PARIS", "France edge South Africa 21-19. (AFP)"),
    (32, "DAKAR", "Faye enacts supplementary budget. (AFP)"),
    (33, "DAR ES SALAAM", "Tanzania joins top five gold holders. (Reuters)"),
    (34, "WORLD", "UN marks World Children's Day. (UN News)"),
    (35, "RIYADH", "Houthis claim airport strike. (Al Jazeera)"),
    (36, "MEXICO CITY", "Nation marks 116th Revolution Day. (AP)"),
]

FIGURES = [
    ("3", "KYIV WATER WORKERS KILLED", "KYIV POST"),
    ("300,000+", "EVACUATED AHEAD OF AKVAN", "IMD"),
    ("~30", "MISSILES FIRED AT KYIV", "KYIV POST"),
    ("-7%", "ASIA'S WORST WEEK SINCE 2020", "REUTERS"),
    ("2.2%", "JAPAN OCT CPI; BOJ EYED", "REUTERS"),
    ("118", "PHILLIPS' HISTORIC CENTURY", "ICC"),
]

REGIONS = [
    ("EUROPE 8", BLUE_CHIP), ("AMERICAS 6", GREEN_CHIP),
    ("ASIA-PACIFIC 11", RED_CHIP), ("MIDEAST 3", BROWN_CHIP),
    ("AFRICA 3", PURPLE_CHIP), ("OCEANIA 3", TEAL_CHIP),
    ("WORLD 2", GREY_CHIP),
]

DATE_CHECK = ("First reported Thursday 19 Nov, so NOT shown as Friday's news: "
              "the Trump-Xi-Putin Shenzhen summit itself - Anthropic's $83 IPO "
              "pricing - ICJ Myanmar verdict - GTA VI's midnight launch - the "
              "$190.4m Van Gogh sale - Voyager 1's one-light-day confirmation - "
              "the EU's 45bn Ukraine loan - Han Duck-soo's acquittal - the "
              "Crimean Bridge attack - the Houthi strike on Riyadh's PIF tower - "
              "Fiji's drought declaration.")


def build():
    s = Sheet(W, H, CREAM)
    t = Type(s)
    M = 28
    CW = W - 2 * M

    # top strip
    t.draw(M, 8, "THE WORLD IN ONE DAY", 12, RED)
    right = "FRIDAY'S NEWS - ONE PAGE - 36 STORIES - 7 REGIONS"
    t.draw(M + CW - t.width(right, 11), 9, right, 11, INK)
    s.rect(M, 28, CW, 2, INK)

    # masthead
    head = "Friday 20 November 2026"
    hw = t.width(head, 66)
    t.draw(M + (CW - hw) / 2, 32, head, 66, INK)
    sub = ("Missiles hit Kyiv - Cyclone Akvan comes ashore - "
           "COP31 deadlocked - Asia's AI sell-off")
    sw = t.width(sub, 12)
    t.draw(M + (CW - sw) / 2, 122, sub, 12, RED)
    s.rect(M, 142, CW, 3, INK)

    # figures band
    fy = 150
    cell = CW / 6.0
    for i, (num, cap1, src) in enumerate(FIGURES):
        x = M + i * cell
        if i:
            s.rect(int(x), fy + 4, 1, 44, (200, 192, 170))
        nw = t.width(num, 26)
        t.draw(x + (cell - nw) / 2, fy, num, 26, RED)
        lines = t.wrap(cap1, 9, cell - 10)[:2]
        for j, ln in enumerate(lines):
            lw = t.width(ln, 9)
            t.draw(x + (cell - lw) / 2, fy + 30 + j * 11, ln, 9, INK)
        sw2 = t.width(src, 8)
        t.draw(x + (cell - sw2) / 2, fy + 30 + 2 * 11, src, 8, GREY)
    s.rect(M, fy + 56, CW, 1, (200, 192, 170))

    # region bar
    ry = 210
    rx = M
    for label, col in REGIONS:
        lw = t.width(label, 10)
        s.rect(int(rx), ry, int(lw + 12), 18, col)
        t.draw(int(rx) + 6, ry + 3, label, 10, (255, 255, 255))
        rx += lw + 12 + 4
    rtext = "ALL STORIES: FRI 20 NOV 2026, ANY TIME ZONE"
    t.draw(M + CW - t.width(rtext, 10), ry + 3, rtext, 10, INK)

    # leads
    ly = 234
    colw = 312
    gap = (CW - 3 * colw) / 2
    for i, (num, kick, head2, deck, fn) in enumerate(LEADS):
        x = M + i * (colw + gap)
        fn(s, int(x), ly, colw, 104)
        t.draw(int(x), ly + 110, num, 11, RED)
        t.draw(int(x) + 26, ly + 110, kick, 11, INK)
        yy = t.para(int(x), ly + 126, head2, 21, INK, colw, leading=26)
        t.para(int(x), yy + 2, deck, 11, INK, colw, leading=14)

    # small cards, two rows of five
    cy0 = 448
    ccol = 191
    cgap = (CW - 5 * ccol) / 4
    for i, (num, kick, head2, deck, fn) in enumerate(CARDS):
        row, col = divmod(i, 5)
        x = M + col * (ccol + cgap)
        y = cy0 + row * 138
        fn(s, int(x), y, ccol, 48)
        t.draw(int(x), y + 52, num, 10, RED)
        t.draw(int(x) + 22, y + 52, kick, 10, INK)
        yy = t.para(int(x), y + 66, head2, 14, INK, ccol, leading=18)
        t.para(int(x), yy + 1, deck, 9.5, INK, ccol, leading=12)

    # map + also
    my = 724
    s.rect(M, my - 6, CW, 1, (200, 192, 170))
    t.draw(M, my - 2, "WHERE IT HAPPENED", 12, RED)
    t.draw(M + 340, my - 2, "ALSO ON FRIDAY 20 NOVEMBER - 23 MORE STORIES", 12, RED)
    draw_map(s, M, my + 18, 330, 190)
    ax = M + 340
    aw = CW - 340
    colw2 = aw / 2 - 6
    yy1 = my + 18
    yy2 = my + 18
    for k, (num, place, text) in enumerate(ALSO):
        if k < 12:
            yy1 = also_item(s, t, int(ax), int(yy1), num, place, text, colw2, cap=9)
            yy1 += 3
        else:
            yy2 = also_item(s, t, int(ax + colw2 + 12), int(yy2), num, place,
                            text, colw2, cap=9)
            yy2 += 3

    # date check
    dy = 950
    s.frame(M, dy - 8, CW, 52, RED, 2)
    t.draw(M + 8, dy - 4, "DATE CHECK", 11, RED)
    dw = t.width("DATE CHECK", 11)
    t.para(M + 8 + dw + 10, dy - 4, DATE_CHECK, 10, INK, CW - dw - 26,
           leading=13)

    # footer
    foot = ("Every story here happened, or was first reported, on Friday 20 November 2026. "
            "Disputed claims are attributed.")
    fw = t.width(foot, 9)
    t.draw(M + (CW - fw) / 2, 1006, foot, 9, GREY)
    return s


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(outdir, exist_ok=True)
    sheet = build()
    path = os.path.join(outdir, "entry.png")
    n = write_png(sheet, path)
    print("wrote %s (%d bytes)" % (path, n))


if __name__ == "__main__":
    main()
