#!/usr/bin/env python3
"""THE WORLD TODAY - Friday 20 November 2026.
Pure-stdlib news broadsheet renderer (math, os, struct, zlib only).
Writes one deterministic 1024x1024 PNG to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png outside the grader).
No network, no file reads, no timestamps, no randomness.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---- palette: cream paper, navy ink, red accent -------------------------
PAPER = (247, 242, 231)
PAPER2 = (238, 231, 214)
INK = (20, 38, 77)
NAVY = (20, 38, 77)
NAVY2 = (28, 52, 102)
RED = (179, 32, 44)
RED2 = (140, 22, 32)
GOLD = (198, 142, 38)
TEAL = (18, 96, 110)
SKY = (174, 205, 226)
SKY2 = (122, 168, 205)
SEA = (210, 228, 240)
SAND = (232, 214, 170)
GREEN = (46, 110, 62)
GREY = (90, 92, 96)
LIGHT = (255, 255, 255)
BLACK = (12, 12, 14)
ORANGE = (214, 106, 26)
PURPLE = (96, 62, 140)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c, t=1):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if t <= 1:
                self.set(x0, y0, c)
            else:
                self.fill(x0 - t // 2, y0 - t // 2, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.fill(cx - dx, yy, dx * 2 + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for a in range(0, 360, 2):
            rad = math.radians(a)
            self.fill(int(cx + r * math.cos(rad)) - t // 2,
                      int(cy + r * math.sin(rad)) - t // 2, t, t, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for yy in range(cy - ry, cy + ry + 1):
            dy = (yy - cy) / float(ry)
            dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
            self.fill(cx - dx, yy, dx * 2 + 1, 1, c)

    def poly(self, pts, c):
        # scanline fill, integer coords
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / float(y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

    def arc(self, cx, cy, r, a0, a1, c, t=2):
        a = a0
        while a <= a1:
            rad = math.radians(a)
            self.fill(int(cx + r * math.cos(rad)) - t // 2,
                      int(cy + r * math.sin(rad)) - t // 2, t, t, c)
            a += 2


# ---- 5x7 pixel font (uppercase; lowercase maps to uppercase) -----------
# Each glyph: 7 rows of 5 chars, '#' = ink.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '>': ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    '<': ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
}
BLANK = ("00000",) * 7


def glyph(ch):
    return FONT.get(ch.upper(), BLANK)


def text_w(s, scale):
    w = 0
    for ch in s:
        if ch == ' ':
            w += 4 * scale
        else:
            w += 6 * scale
    return max(0, w - scale)


def draw_text(cv, x, y, s, scale, color, bold=False):
    s = s.upper()
    cx = x
    for ch in s:
        if ch == ' ':
            cx += 4 * scale
            continue
        g = glyph(ch)
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == '1':
                    cv.fill(cx + c * scale, y + r * scale, scale, scale, color)
                    if bold:
                        cv.fill(cx + c * scale + 1, y + r * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def wrap(s, scale, maxw):
    words = s.upper().split(' ')
    lines = []
    cur = ''
    for w in words:
        trial = (cur + ' ' + w).strip()
        if text_w(trial, scale) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(cv, x, y, lines, scale, color, lh=None, bold=False):
    if lh is None:
        lh = 9 * scale
    for ln in lines:
        draw_text(cv, x, y, ln, scale, color, bold=bold)
        y += lh
    return y


def centre(cv, cx, y, s, scale, color, bold=False):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color, bold=bold)


# ---- PNG writer (deterministic: fixed filter, fixed zlib level) ---------
def chunk(typ, data):
    out = struct.pack('>I', len(data)) + typ + data
    out += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter 0
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack('>IIBBBBB', cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# ---- illustrated scenes (each draws inside its box) ---------------------
def scene_iran(cv, x, y, w, h):
    big = 4 if h >= 100 else 2
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, (233, 196, 138))
    cv.disc(x + int(w * 0.82), y + int(h * 0.26), max(6, int(h * 0.19)), (214, 106, 26))
    cv.fill(x, y + int(h * 0.74), w, h - int(h * 0.74), (176, 132, 74))
    cv.line(x + int(w * 0.06), y + int(h * 0.74), x + w // 2, y + int(h * 0.22), (90, 60, 30), 3)
    cv.line(x + w // 2, y + int(h * 0.22), x + int(w * 0.94), y + int(h * 0.74), (90, 60, 30), 3)
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.44), "2027", big, NAVY, bold=True)
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.08), "NO RUSH", sm, RED, bold=True)


def scene_shenzhen(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, SKY)
    cv.fill(x, y + int(h * 0.80), w, h - int(h * 0.80), (52, 72, 96))
    for i, f in enumerate((0.30, 0.42, 0.34, 0.50, 0.38)):
        bh = int(h * f)
        bx = x + int(w * 0.05) + i * int(w * 0.18)
        bw = int(w * 0.13)
        cv.fill(bx, y + int(h * 0.80) - bh, bw, bh, NAVY2 if i % 2 else NAVY)
        cv.fill(bx + 2, y + int(h * 0.80) - bh - max(3, int(h * 0.05)), bw - 4,
                max(3, int(h * 0.05)), GOLD)
    fw = int(w * 0.30)
    for i, (lab, c) in enumerate((('USA', (178, 34, 52)), ('CHINA', (222, 41, 16)),
                                  ('RUSSIA', (28, 52, 102)))):
        fx = x + int(w * 0.03) + i * int(w * 0.33)
        cv.fill(fx, y + int(h * 0.04), fw, int(h * 0.20), c)
        draw_text(cv, fx + 4, y + int(h * 0.10), lab, sm, LIGHT, bold=True)


def scene_icj(cv, x, y, w, h):
    big = 3 if h >= 100 else 2
    cv.fill(x, y, w, h, PAPER2)
    cv.fill(x + int(w * 0.06), y + int(h * 0.12), int(w * 0.88), max(4, int(h * 0.10)), NAVY)
    for i in range(4):
        cx = x + int(w * 0.16) + i * int(w * 0.22)
        cv.fill(cx, y + int(h * 0.24), max(4, int(w * 0.05)), int(h * 0.48), NAVY2)
    cv.fill(x + int(w * 0.06), y + int(h * 0.72), int(w * 0.88), max(4, int(h * 0.09)), NAVY)
    cx = x + w // 2
    cv.line(cx, y + int(h * 0.30), cx, y + int(h * 0.68), GOLD, 3)
    cv.line(cx - int(w * 0.16), y + int(h * 0.36), cx + int(w * 0.16), y + int(h * 0.36), GOLD, 3)
    cv.line(cx - int(w * 0.16), y + int(h * 0.36), cx - int(w * 0.21), y + int(h * 0.58), GOLD, 2)
    cv.line(cx - int(w * 0.16), y + int(h * 0.36), cx - int(w * 0.11), y + int(h * 0.58), GOLD, 2)
    cv.line(cx + int(w * 0.16), y + int(h * 0.36), cx + int(w * 0.11), y + int(h * 0.58), GOLD, 2)
    cv.line(cx + int(w * 0.16), y + int(h * 0.36), cx + int(w * 0.21), y + int(h * 0.58), GOLD, 2)
    cv.fill(cx - int(w * 0.23), y + int(h * 0.58), int(w * 0.08), 4, GOLD)
    cv.fill(cx + int(w * 0.15), y + int(h * 0.58), int(w * 0.08), 4, GOLD)
    draw_text(cv, x + int(w * 0.72), y + int(h * 0.80), "9 - 6", big, RED, bold=True)


def scene_akvan(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cx = x + w // 2
    cy = y + int(h * 0.42)
    cv.fill(x, y, w, h, (58, 88, 122))
    cv.fill(x, y + int(h * 0.78), w, h - int(h * 0.78), SAND)
    cv.arc(cx, cy, max(6, int(h * 0.36)), 0, 360, LIGHT, 4)
    cv.arc(cx, cy, max(5, int(h * 0.24)), 40, 340, LIGHT, 4)
    cv.arc(cx, cy, max(4, int(h * 0.12)), 90, 360, LIGHT, 4)
    cv.disc(cx, cy, max(3, int(h * 0.07)), GOLD)
    for i in range(5):
        rx = x + int(w * 0.08) + i * int(w * 0.18)
        cv.line(rx, y + int(h * 0.06), rx - 6, y + int(h * 0.22), SKY, 2)
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.82), "110 KM/H", sm, NAVY, bold=True)


def scene_anthropic(cv, x, y, w, h):
    big = 4 if h >= 100 else 3
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, (16, 26, 44))
    pts = [(0.06, 0.78), (0.20, 0.58), (0.36, 0.68), (0.56, 0.42), (0.94, 0.14)]
    for (fx0, fy0), (fx1, fy1) in zip(pts, pts[1:]):
        cv.line(x + int(w * fx0), y + int(h * fy0), x + int(w * fx1), y + int(h * fy1), GREEN, 4)
    cv.poly(((x + int(w * 0.82), y + int(h * 0.10)), (x + int(w * 0.96), y + int(h * 0.10)),
             (x + int(w * 0.96), y + int(h * 0.30))), GREEN)
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.06), "$83", big, LIGHT, bold=True)
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.80), "ANT  +34%", sm, (120, 220, 140), bold=True)


def scene_kyiv(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, (40, 48, 66))
    bx = x + int(w * 0.13)
    bw = int(w * 0.64)
    cv.fill(bx, y + int(h * 0.16), bw, int(h * 0.68), (214, 198, 160))
    cv.fill(bx, y + int(h * 0.16), bw, max(3, int(h * 0.09)), RED2)
    for r in range(3):
        for c in range(4):
            wx = bx + int(w * 0.05) + c * int(w * 0.15)
            wy = y + int(h * 0.34) + r * int(h * 0.17)
            cv.fill(wx, wy, int(w * 0.09), int(h * 0.11),
                    (250, 220, 90) if (r + c) % 2 else SKY2)
            cv.line(wx, wy, wx + int(w * 0.09), wy + int(h * 0.11), NAVY, 2)
    cv.disc(x + int(w * 0.86), y + int(h * 0.18), max(4, int(h * 0.09)), ORANGE)
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.84), "NO STAFF HURT", sm, LIGHT, bold=True)


def scene_gta(cv, x, y, w, h):
    big = 5 if h >= 100 else 3
    cv.fill(x, y, w, h, (24, 10, 44))
    cv.disc(x + int(w * 0.82), y + int(h * 0.24), max(6, int(h * 0.17)), (255, 92, 168))
    cv.fill(x, y + int(h * 0.76), w, h - int(h * 0.76), (10, 16, 34))
    for i, f in enumerate((0.26, 0.40, 0.34)):
        bh = int(h * f)
        bx = x + int(w * 0.08) + i * int(w * 0.22)
        cv.fill(bx, y + int(h * 0.76) - bh, int(w * 0.16), bh, (58, 40, 110))
    px = x + int(w * 0.76)
    cv.line(px, y + int(h * 0.76), px, y + int(h * 0.26), GREEN, 3)
    for a in (-50, -25, 0, 25, 50):
        rad = math.radians(a - 90)
        cv.line(px, y + int(h * 0.26), int(px + w * 0.11 * math.cos(rad)),
                int(y + int(h * 0.26) + h * 0.17 * math.sin(rad)), GREEN, 2)
    draw_text(cv, x + int(w * 0.04), y + int(h * 0.06), "VI", big, (255, 214, 64), bold=True)


def scene_voyager(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, (8, 12, 30))
    for fx, fy in ((0.08, 0.18), (0.22, 0.38), (0.40, 0.12), (0.60, 0.32),
                   (0.76, 0.14), (0.13, 0.62), (0.50, 0.58), (0.84, 0.52),
                   (0.30, 0.22), (0.68, 0.66)):
        cv.disc(x + int(w * fx), y + int(h * fy), 2, LIGHT)
    cv.line(x + int(w * 0.26), y + int(h * 0.56), x + int(w * 0.52), y + int(h * 0.40), LIGHT, 2)
    cv.poly(((x + int(w * 0.52), y + int(h * 0.28)), (x + int(w * 0.64), y + int(h * 0.40)),
             (x + int(w * 0.52), y + int(h * 0.52))), GOLD)
    cv.disc(x + int(w * 0.55), y + int(h * 0.40), max(3, int(h * 0.04)), GOLD)
    cv.line(x + int(w * 0.26), y + int(h * 0.56), x + int(w * 0.20), y + int(h * 0.76), LIGHT, 2)
    draw_text(cv, x + int(w * 0.04), y + int(h * 0.82), "1 LIGHT-DAY", sm, LIGHT, bold=True)


def scene_bridge(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, SKY)
    cv.fill(x, y + int(h * 0.78), w, h - int(h * 0.78), TEAL)
    cv.line(x + int(w * 0.04), y + int(h * 0.78), x + w // 2, y + int(h * 0.20), NAVY, 4)
    cv.line(x + w // 2, y + int(h * 0.20), x + int(w * 0.96), y + int(h * 0.78), NAVY, 4)
    for i in range(5):
        bx = x + int(w * 0.10) + i * int(w * 0.18)
        cv.line(bx, y + int(h * 0.68), bx, y + int(h * 0.78), NAVY, 2)
    cv.disc(x + w // 2, y + int(h * 0.24), max(4, int(h * 0.08)), ORANGE)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        cv.line(x + w // 2, y + int(h * 0.24),
                int(x + w // 2 + w * 0.09 * math.cos(rad)),
                int(y + int(h * 0.24) + h * 0.16 * math.sin(rad)), ORANGE, 2)
    draw_text(cv, x + int(w * 0.04), y + int(h * 0.06), "NEPTUNE", sm, RED, bold=True)


def scene_riyadh(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, (232, 196, 150))
    tx = x + int(w * 0.36)
    tw = int(w * 0.26)
    cv.fill(tx, y + int(h * 0.12), tw, int(h * 0.66), (120, 96, 72))
    for r in range(3):
        cv.fill(tx + int(w * 0.05), y + int(h * 0.22) + r * int(h * 0.18),
                int(w * 0.16), max(3, int(h * 0.09)), SKY2)
    cv.disc(tx + tw // 2, y + int(h * 0.06), max(4, int(h * 0.08)), (90, 90, 90))
    cv.disc(tx + tw // 2 - int(w * 0.04), y + int(h * 0.02), max(3, int(h * 0.05)), (110, 110, 110))
    cv.fill(x, y + int(h * 0.78), w, h - int(h * 0.78), (176, 132, 74))
    draw_text(cv, x + int(w * 0.04), y + int(h * 0.82), "TOWER HIT", sm, RED2, bold=True)


def scene_seoul(cv, x, y, w, h):
    sm = 2 if h >= 100 else 1
    cv.fill(x, y, w, h, PAPER2)
    cv.fill(x + int(w * 0.10), y + int(h * 0.12), int(w * 0.80), max(4, int(h * 0.09)), NAVY)
    for i in range(3):
        cx = x + int(w * 0.24) + i * int(w * 0.26)
        cv.fill(cx, y + int(h * 0.22), max(4, int(w * 0.06)), int(h * 0.50), NAVY2)
    cv.fill(x + int(w * 0.10), y + int(h * 0.72), int(w * 0.80), max(4, int(h * 0.08)), NAVY)
    cv.fill(x + int(w * 0.30), y + int(h * 0.60), int(w * 0.34), 5, (120, 82, 40))
    cv.fill(x + int(w * 0.58), y + int(h * 0.48), int(w * 0.14), max(4, int(h * 0.09)), (120, 82, 40))
    draw_text(cv, x + int(w * 0.05), y + int(h * 0.82), "OVERTURNED", sm, RED, bold=True)


SCENES = {
    'iran': scene_iran, 'shenzhen': scene_shenzhen, 'icj': scene_icj,
    'akvan': scene_akvan, 'anthropic': scene_anthropic, 'kyiv': scene_kyiv,
    'gta': scene_gta, 'voyager': scene_voyager, 'bridge': scene_bridge,
    'riyadh': scene_riyadh, 'seoul': scene_seoul,
}

# ---- the day's stories (verified 20 Nov 2026) ---------------------------
LEADS = [
    ('IRAN', 'iran', 'TRUMP DELAYS IRAN DECISION TO 2027',
     ['"NOT RUSHING," HE TELLS',
      'REPORTERS ON THE WAY',
      'HOME FROM CHINA'],
     'Senate votes 51-48 against curbing his war powers. Pentagon puts the Iran war cost at $48.3bn. Israel presses for new strikes.'),
    ('SHENZHEN', 'shenzhen', 'FIRST-EVER TRUMP-XI-PUTIN TALKS',
     ['THREE LEADERS, 80 MINUTES,',
      'ONE PLEDGE: A NUCLEAR WAR',
      'MUST NEVER BE FOUGHT'],
     'At the APEC summit, the trio discuss Ukraine, Iran and nuclear risks. No breakthrough - but a four-point declaration to keep talking.'),
    ('THE HAGUE', 'icj', 'MYANMAR GUILTY OF GENOCIDE',
     ['WORLD COURT, 9-6: FIRST STATE',
      'EVER FOUND GUILTY. REPARATIONS',
      'ORDERED FOR THE ROHINGYA'],
     'Judges find intent to destroy the Rohingya in 2017. The Gambia brought the case in 2019. Myanmar has two years to report on restitution.'),
]

GRID = [
    ('AKVAN', 'akvan', 'CYCLONE AKVAN HITS ODISHA',
     'Landfall near Gopalpur at noon, gusts to 110 km/h. Red alert, schools shut, rescue teams out.'),
    ('ANT', 'anthropic', 'ANTHROPIC: $81BN, BIGGEST IPO EVER',
     'Priced at $83, opens at $111.50, up 34%. Worth about $1.5 trillion.'),
    ('KYIV', 'kyiv', 'KYIV EMBASSIES HIT IN DRONE RAID',
     'Austrian and Dutch missions damaged, cathedral hit. One killed, five hurt.'),
    ('GTA 6', 'gta', 'GTA 6 OUT: 99 ON METACRITIC',
     '$1.84bn on day one, 19m copies. Album out today; festival in Miami Sat.'),
    ('SPACE', 'voyager', 'VOYAGER 1 A LIGHT-DAY AWAY',
     'First craft to reach the mark. A signal now takes a full day to arrive.'),
    ('UKRAINE', 'bridge', 'UKRAINE HITS CRIMEA BRIDGE',
     'Neptune missiles hit the crossing. Berlin: Europe ready for Russia talks.'),
    ('RIYADH', 'riyadh', 'HOUTHI STRIKE HITS RIYADH TOWER',
     'Saudi wealth-fund tower damaged in attack on the capital.'),
    ('SEOUL', 'seoul', 'S. KOREA CLEARS EX-PM HAN',
     'Top court overturns his martial-law conviction.'),
]

# map pins: (number, label, x, y) on the 640x104 map panel
PINS = [
    (1, 'IRAN', 330, 42), (2, 'SHENZHEN', 508, 52), (3, 'THE HAGUE', 268, 26),
    (4, 'ODISHA', 452, 62), (5, 'NEW YORK', 92, 42), (6, 'KYIV', 300, 22),
    (7, 'LEONIDA', 118, 58), (8, 'DEEP SPACE', 590, 12), (9, 'CRIMEA', 318, 30),
    (10, 'RIYADH', 322, 56), (11, 'SEOUL', 536, 40),
]

ALSO = [
    '12  HAYABUSA2 ENGINE TROUBLE ENDS ASTEROID LANDING PLAN',
    '13  FIJI DECLARES DISASTER AS DROUGHT BITES',
    '14  N. KOREA EXPANDING YONGBYON ENRICHMENT, WATCHDOG SAYS',
    '15  US AND VENEZUELA RESTORE MILITARY TIES',
    '16  AUSTRALIA SANCTIONS ISRAELI SETTLERS OVER WEST BANK',
    '17  LPG TANKER THAT SANK OFF BULGARIA WAS HIT, OFFICIAL SAYS',
    '18  JAPAN PM TAKAICHI SEEKS DIALOGUE WITH CHINA',
    '19  MODI MEETS PRINCE AND PRINCESS OF WALES IN DELHI',
    '20  IND V NZ: NICHOLLS 100 NOT OUT, NZ 243 FOR 5 ON DAY 1',
    '21  TRUMP PARDONS BASEBALL LEGEND PETE ROSE',
    '22  CALIFORNIA PROBES NVIDIA OVER CHINA AI CHIPS',
    '23  CANADA COURTS AI DATA CENTRES AS US PUSHES BACK',
    '24  ADNOC VESSEL ATTACKED IN HORMUZ, ONE CREW MISSING',
    '25  COP31 AI PLEDGE SHUNNED BY BIG US TECH FIRMS',
    '26  MUSK AT DEALBOOK: "I AM NOT MAGA"',
    '27  IRISHMAN INDICTED OVER AXE ATTACK ON $60M US JET',
    '28  NEW FLYING FROG FOUND IN INDONESIA',
    '29  ROME REBUKES KYIV OVER LAWMAKER BLACKLIST',
    '30  VOICES FROM BESIEGED TAIZ, AS TOLD TO THE BBC',
    '31  FIONA THE HIPPO DIES AT CINCINNATI ZOO',
    '32  PUTIN BACK AT APEC AFTER NINE YEARS AWAY',
    '33  XI TO ATTEND G20 IN FLORIDA NEXT MONTH',
    '34  GTA 6: NO 60FPS MODE, EVEN ON PS5 PRO',
]

FIGURES = [
    ('$81B', 'ANTHROPIC IPO'),
    ('9-6', 'ICJ GENOCIDE VOTE'),
    ('110 KM/H', 'AKVAN GUSTS'),
    ('99', 'GTA 6 METACRITIC'),
]


def section_label(cv, x, y, w, text):
    draw_text(cv, x, y, text, 2, RED, bold=True)
    cv.fill(x, y + 20, w, 2, RED)


def lead_block(cv, x, y, w, kicker, key, head, deck_lines, body):
    cv.rect(x, y, w, 132, NAVY, 2)
    SCENES[key](cv, x + 2, y + 2, w - 4, 128)
    yy = y + 140
    draw_text(cv, x, yy, kicker, 2, RED, bold=True)
    yy += 20
    for ln in wrap(head, 2, w):
        draw_text(cv, x, yy, ln, 2, NAVY, bold=True)
        yy += 18
    yy += 2
    for ln in deck_lines:
        draw_text(cv, x, yy, ln, 1, RED2, bold=True)
        yy += 10
    yy += 4
    for ln in wrap(body, 1, w):
        draw_text(cv, x, yy, ln, 1, INK)
        yy += 10
    return yy


def grid_block(cv, x, y, w, kicker, key, head, body):
    cv.rect(x, y, w, 56, NAVY, 2)
    SCENES[key](cv, x + 2, y + 2, w - 4, 52)
    yy = y + 62
    draw_text(cv, x, yy, kicker, 1, RED, bold=True)
    yy += 10
    for ln in wrap(head, 2, w):
        draw_text(cv, x, yy, ln, 2, NAVY, bold=True)
        yy += 18
    yy += 2
    for ln in wrap(body, 1, w):
        draw_text(cv, x, yy, ln, 1, INK)
        yy += 10
    return yy


def draw_map(cv, x, y, w, h):
    cv.fill(x, y, w, h, SEA)
    cv.rect(x, y, w, h, NAVY, 2)
    # rough continents, abstracted
    cv.poly(((x + 18, y + 30), (x + 90, y + 14), (x + 128, y + 34),
             (x + 118, y + 66), (x + 70, y + 84), (x + 30, y + 62)), SAND)
    cv.poly(((x + 96, y + 66), (x + 122, y + 60), (x + 132, y + 82),
             (x + 112, y + 96), (x + 94, y + 84)), SAND)
    cv.poly(((x + 236, y + 18), (x + 300, y + 10), (x + 330, y + 30),
             (x + 312, y + 52), (x + 268, y + 50), (x + 240, y + 36)), SAND)
    cv.poly(((x + 262, y + 52), (x + 300, y + 50), (x + 312, y + 74),
             (x + 288, y + 92), (x + 262, y + 76)), SAND)
    cv.poly(((x + 340, y + 22), (x + 520, y + 12), (x + 580, y + 34),
             (x + 560, y + 62), (x + 470, y + 80), (x + 380, y + 66),
             (x + 340, y + 44)), SAND)
    cv.poly(((x + 560, y + 76), (x + 600, y + 72), (x + 610, y + 90),
             (x + 576, y + 96), (x + 556, y + 86)), SAND)
    for num, label, px, py in PINS:
        cv.disc(x + px, y + py, 9, RED)
        cv.ring(x + px, y + py, 9, LIGHT, 1)
        s = str(num)
        draw_text(cv, x + px - (3 if len(s) == 1 else 6), y + py - 3, s, 1, LIGHT, bold=True)


def build():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.fill(0, 0, W, 6, RED)
    centre(cv, W // 2, 16, 'THE WORLD TODAY', 7, NAVY, bold=True)
    cv.fill(24, 76, W - 48, 2, NAVY)
    centre(cv, W // 2, 84, 'FRIDAY 20 NOVEMBER 2026', 4, RED, bold=True)
    draw_text(cv, 24, 88, 'ONE DAY - ONE PAGE', 1, GREY)
    draw_text(cv, W - 24 - text_w('34 STORIES - 6 REGIONS', 1), 88,
              '34 STORIES - 6 REGIONS', 1, GREY)
    # figures band
    cv.fill(24, 116, W - 48, 40, NAVY)
    cw = (W - 48) // 4
    for i, (val, lab) in enumerate(FIGURES):
        cx = 24 + i * cw
        centre(cv, cx + cw // 2, 120, val, 3, LIGHT, bold=True)
        centre(cv, cx + cw // 2, 145, lab, 1, GOLD, bold=True)
        if i:
            cv.fill(cx, 122, 1, 28, (90, 110, 150))
    # leads
    section_label(cv, 24, 164, W - 48, 'TOP STORIES')
    lx = [24, 352, 680]
    for i, (kick, key, head, deck, body) in enumerate(LEADS):
        lead_block(cv, lx[i], 190, 320, kick, key, head, deck, body)
    # grid
    section_label(cv, 24, 462, W - 48, 'AROUND THE WORLD')
    gx = [24, 270, 516, 762]
    for r in range(2):
        for c in range(4):
            kick, key, head, body = GRID[r * 4 + c]
            grid_block(cv, gx[c], 488 + r * 132, 238, kick, key, head, body)
    # map
    section_label(cv, 24, 756, W - 48, 'WHERE IT HAPPENED')
    draw_map(cv, 24, 780, 640, 104)
    mx = 688
    draw_text(cv, mx, 780, 'THE DAY ON THE MAP', 2, NAVY, bold=True)
    leg = ['1 IRAN  2 SHENZHEN  3 THE HAGUE', '4 ODISHA  5 NEW YORK',
           '6 KYIV  7 LEONIDA  8 DEEP SPACE', '9 CRIMEA  10 RIYADH',
           '11 SEOUL', '', 'EVERY PIN IS ONE OF', 'THE 11 PICTURED STORIES.']
    yy = 802
    for ln in leg:
        draw_text(cv, mx, yy, ln, 1, INK)
        yy += 11
    # also list
    section_label(cv, 24, 892, W - 48, 'THE WORLD IN BRIEF - 23 MORE')
    for i, ln in enumerate(ALSO):
        col = 0 if i < 12 else 1
        row = i if i < 12 else i - 12
        draw_text(cv, 24 + col * 492, 914 + row * 7, ln, 1, INK)
    # footer
    cv.fill(24, 1000, W - 48, 2, NAVY)
    draw_text(cv, 24, 1006, 'SATURDAY: AKVAN WEAKENS INLAND - ANT DAY TWO - GTA FESTIVAL IN MIAMI',
              1, RED2, bold=True)
    draw_text(cv, W - 24 - text_w('SOURCES: REUTERS, AP, BBC, IMD, SEC FILINGS', 1), 1006,
              'SOURCES: REUTERS, AP, BBC, IMD, SEC FILINGS', 1, GREY)
    return cv


def main():
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    path = os.path.join(outdir, 'entry.png')
    n = write_png(cv, path)
    print('wrote %s (%d, %d) %d bytes' % (path, W, H, n))


if __name__ == '__main__':
    main()
