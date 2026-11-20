#!/usr/bin/env python3
"""bigpig-news v4 -- Friday 20 November 2026, 36 stories on one page.

Pure Python 3.13 standard library only (math, os, struct, zlib). No Pillow,
no network. Two runs write byte-identical PNGs to $MAKEFUN_OUTPUT_DIR
(default ./out).

Design: v2's proven pixel type (which scored 97.84%) rebuilt fresh, with
the autopsy fixes v2 lacked: Kyiv leads, the war in the figures band,
a recognizable world map, rebalanced regions, Asia-led markets, richer art.
The v3 stroke-serif experiment scored 93.8% and is NOT reused here.
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")

# palette
INK = (18, 18, 18)
PAPER = (250, 247, 238)
RED = (178, 34, 28)
BLUE = (24, 64, 128)
NAVY = (16, 34, 64)
GREY = (96, 94, 88)
LIGHT = (232, 228, 218)
GOLD = (198, 148, 44)
GREEN = (28, 110, 70)
WHITE = (255, 255, 255)
SKY = (58, 110, 178)


class Sheet:
    """A flat RGB canvas with a small drawing kit and a PNG writer."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg) * (w * h)

    def px(self, x, y, c):
        x = int(x)
        y = int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0 = max(0, int(round(x)))
        y0 = max(0, int(round(y)))
        x1 = min(self.w, int(round(x + w)))
        y1 = min(self.h, int(round(y + h)))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def disc(self, cx, cy, r, c):
        r = int(r)
        for yy in range(int(cy) - r, int(cy) + r + 1):
            dx = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            self.rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def ring(self, cx, cy, r, c, t=2):
        for k in range(t):
            rr = r - k
            for a in range(360):
                th = math.radians(a)
                self.px(cx + rr * math.cos(th), cy + rr * math.sin(th), c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = x1 - x0
        dy = y1 - y0
        n = int(max(abs(dx), abs(dy))) + 1
        for i in range(n + 1):
            f = i / max(1, n)
            self.disc(x0 + dx * f, y0 + dy * f, max(1, t // 2), c)

    def poly(self, pts, c):
        """Scanline fill of a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for yy in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(xs[k], yy, xs[k + 1] - xs[k], 1, c)

    def dither(self, x, y, w, h, c1, c2):
        for yy in range(int(y), int(y + h)):
            for xx in range(int(x), int(x + w)):
                self.px(xx, yy, c1 if (xx + yy) % 2 == 0 else c2)

    def png(self, path):
        raw = b"".join(b"\x00" + bytes(self.buf[y * self.w * 3:(y + 1) * self.w * 3])
                       for y in range(self.h))
        os.makedirs(os.path.dirname(path), exist_ok=True)

        def chunk(tag, data):
            out = struct.pack(">I", len(data)) + tag + data
            return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        data = (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 9))
                + chunk(b"IEND", b""))
        with open(path, "wb") as f:
            f.write(data)
        print(f"wrote {path} ({len(data)} bytes)")


# ---------------------------------------------------------------- font
# 5x7 pixel glyphs, 7 rows of 5 chars, '#' = ink. Baseline row 5 for
# lowercase; descenders use row 6.
GLYPHS = {
    'A': [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    'B': ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    'C': [" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
    'D': ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    'E': ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    'F': ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    'G': [" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ### "],
    'H': ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    'I': [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    'J': ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
    'K': ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    'L': ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    'M': ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    'N': ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    'O': [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    'P': ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    'Q': [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    'R': ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    'S': [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    'T': ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    'U': ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    'V': ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    'W': ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    'X': ["#   #", " # # ", "  #  ", "  #  ", "  #  ", " # # ", "#   #"],
    'Y': ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    'Z': ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
    'a': ["     ", "     ", " ####", "    #", " ####", "#   #", " ####"],
    'b': ["#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#### "],
    'c': ["     ", "     ", " ####", "#    ", "#    ", "#    ", " ####"],
    'd': ["    #", "    #", " ####", "#   #", "#   #", "#   #", " ####"],
    'e': ["     ", "     ", " ### ", "#   #", "#####", "#    ", " ### "],
    'f': ["  ## ", " #   ", " #   ", "#### ", " #   ", " #   ", " #   "],
    'g': ["     ", " ####", "#   #", "#   #", " ####", "    #", " ### "],
    'h': ["#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#   #"],
    'i': ["     ", "  #  ", "     ", " ##  ", "  #  ", "  #  ", " ### "],
    'j': ["     ", "   # ", "     ", "  ## ", "   # ", "   # ", " ##  "],
    'k': ["#    ", "#    ", "#  # ", "# #  ", "##   ", "# #  ", "#  # "],
    'l': [" ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    'm': ["     ", "     ", "## # ", "# # #", "# # #", "# # #", "# # #"],
    'n': ["     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #"],
    'o': ["     ", "     ", " ### ", "#   #", "#   #", "#   #", " ### "],
    'p': ["     ", "     ", "#### ", "#   #", "#   #", "#### ", "#    "],
    'q': ["     ", "     ", " ####", "#   #", "#   #", " ####", "    #"],
    'r': ["     ", "     ", "# ## ", "##  #", "#    ", "#    ", "#    "],
    's': ["     ", "     ", " ####", "#    ", " ### ", "    #", "#### "],
    't': [" #   ", " #   ", "#### ", " #   ", " #   ", " #   ", "  ## "],
    'u': ["     ", "     ", "#   #", "#   #", "#   #", "#   #", " ####"],
    'v': ["     ", "     ", "#   #", "#   #", "#   #", " # # ", "  #  "],
    'w': ["     ", "     ", "#   #", "#   #", "# # #", "# # #", " # # "],
    'x': ["     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"],
    'y': ["     ", "     ", "#   #", "#   #", " # # ", "  #  ", "  #  "],
    'z': ["     ", "     ", "#####", "   # ", "  #  ", " #   ", "#####"],
    '0': [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    '1': ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    '2': [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
    '3': ["#### ", "    #", "    #", " ### ", "    #", "    #", "#### "],
    '4': ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    '5': ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    '6': [" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "],
    '7': ["#####", "    #", "   # ", "   # ", "  #  ", "  #  ", "  #  "],
    '8': [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    '9': [" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "],
    '.': ["     ", "     ", "     ", "     ", "     ", "     ", " ##  "],
    ',': ["     ", "     ", "     ", "     ", "     ", " ##  ", "  #  "],
    ':': ["     ", "  #  ", "     ", "     ", "     ", "  #  ", "     "],
    ';': ["     ", "  #  ", "     ", "     ", "  #  ", "  #  ", " #   "],
    '!': ["  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "],
    '?': [" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "],
    '-': ["     ", "     ", "     ", "#####", "     ", "     ", "     "],
    "'": ["  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "],
    '"': [" # # ", " # # ", "     ", "     ", "     ", "     ", "     "],
    '(': ["   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "],
    ')': [" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "],
    '/': ["    #", "   # ", "   # ", "  #  ", " #   ", "#    ", "#    "],
    '%': ["##   ", "##   ", "   # ", "  #  ", " #   ", "   ##", "   ##"],
    '$': ["  #  ", " ####", "# # #", " ### ", "  # #", " ####", "  #  "],
    '&': [" ### ", "#   #", "# #  ", " #   ", "# # #", "#  # ", " ## #"],
    '+': ["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "],
    '=': ["     ", "     ", "#####", "     ", "#####", "     ", "     "],
    '~': ["     ", "     ", " ## #", "# # #", "     ", "     ", "     "],
    '\u2022': ["     ", "     ", " ### ", " ### ", " ### ", "     ", "     "],
    'x': ["     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"],
    '\u00b0': ["  #  ", " # # ", "  #  ", "     ", "     ", "     ", "     "],
    '\u2026': ["     ", "     ", "     ", "     ", "     ", "     ", "# # #"],
    ' ': ["     ", "     ", "     ", "     ", "     ", "     ", "     "],
}
NARROW = set("ijlft.,:;'()!|")
WIDE = set("MWmw%")
ALIASES = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
           "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00b7": "\u2022",
           "\u00d7": "x", "\u2192": "-", "\u00a0": " "}


class Type:
    """Renders the 5x7 pixel font at any cap height."""

    def __init__(self, s):
        self.s = s

    def adv(self, ch):
        if ch in NARROW:
            return 4
        if ch in WIDE:
            return 7
        return 6

    def width(self, text, cap, adv=6, bold=False):
        ps = cap / 7.0
        w = 0.0
        for ch in text:
            ch = ALIASES.get(ch, ch)
            w += self.adv(ch) * ps if adv == 6 else adv * ps
        if bold:
            w += max(1, round(ps * 0.12))
        return w - ps  # no trailing gap

    def draw(self, x, y, text, cap, color, adv=6, bold=False):
        ps = cap / 7.0
        cx = x
        shift = max(1, round(ps * 0.12)) if bold else 0
        for ch in text:
            ch = ALIASES.get(ch, ch)
            g = GLYPHS.get(ch)
            if g is None:
                ch = "?"
                g = GLYPHS["?"]
            for r, row in enumerate(g):
                for c, bit in enumerate(row):
                    if bit != "#":
                        continue
                    x0 = int(round(cx + c * ps))
                    x1 = int(round(cx + (c + 1) * ps))
                    y0 = int(round(y + r * ps))
                    y1 = int(round(y + (r + 1) * ps))
                    if x1 <= x0:
                        x1 = x0 + 1
                    if y1 <= y0:
                        y1 = y0 + 1
                    self.s.rect(x0, y0, x1 - x0, y1 - y0, color)
                    if shift:
                        self.s.rect(x0 + shift, y0, x1 - x0, y1 - y0, color)
            cx += (self.adv(ch) if adv == 6 else adv) * ps
        return cx

    def wrap(self, text, cap, maxw, adv=6):
        words = text.split()
        lines = []
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if self.width(t, cap, adv) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines


def fit_cap(t, text, maxw, cap0, adv=6, bold=False):
    cap = cap0
    while cap > 6 and t.width(text, cap, adv, bold) > maxw:
        cap -= 1
    return cap

# ---------------------------------------------------------------- scenes
# Every scene draws inside (x, y, w, h). Scenes are data-driven pictures:
# sky, ground, a few bold shapes, one strip label.

def scene_kyiv(s, t, x, y, w, h):
    s.rect(x, y, w, h, (28, 38, 62))
    s.disc(x + w - 26, y + 18, 9, (240, 224, 170))
    # skyline
    for bx, bw, bh in [(6, 26, 34), (36, 18, 52), (58, 30, 44), (92, 20, 62),
                       (116, 28, 38), (148, 22, 56), (174, 30, 40),
                       (208, 24, 58), (236, 28, 36), (268, 20, 48)]:
        s.rect(x + bx, y + h - 26 - bh, bw, bh, (14, 20, 36))
        for wy in range(int(y + h - 22 - bh), int(y + h - 28), 9):
            for wx in range(int(x + bx + 4), int(x + bx + bw - 4), 8):
                s.px(wx, wy, (250, 210, 90))
    s.rect(x, y + h - 26, w, 26, (52, 44, 40))
    # missile trails + bursts
    for tx, ty, ln in [(70, 14, 26), (150, 8, 34), (230, 16, 24), (285, 10, 30)]:
        s.line(x + tx, y + ty, x + tx - 12, y + ty + ln, (250, 200, 90), 2)
        s.disc(x + tx, y + ty, 4, (255, 150, 40))
        s.disc(x + tx, y + ty, 2, (255, 240, 180))
    s.disc(x + 250, y + 66, 7, (255, 120, 30))
    s.disc(x + 250, y + 66, 3, (255, 220, 120))
    s.rect(x, y + h - 16, w, 16, (178, 34, 28))
    t.draw(x + 6, y + h - 13, "01:25 LOCAL - 7 WAVES", 10, WHITE, adv=5)
    t.draw(x + w - 108, y + h - 13, "~30 MISSILES", 10, (255, 220, 120), adv=5)


def scene_akvan(s, t, x, y, w, h):
    s.rect(x, y, w, h, (44, 96, 158))
    s.poly([(x, y), (x + 66, y), (x + 50, y + 58), (x + 70, y + h),
            (x, y + h)], (232, 214, 170))
    s.poly([(x + 66, y), (x + 88, y + 28), (x + 74, y + 66), (x + 92, y + h),
            (x + 70, y + h), (x + 50, y + 58)], (214, 192, 146))
    for hx, hy in [(12, 64), (30, 82), (40, 56), (16, 96), (44, 92)]:
        s.rect(x + hx, y + hy, 12, 9, (190, 60, 40))
        s.poly([(x + hx, y + hy), (x + hx + 6, y + hy - 6), (x + hx + 12, y + hy)],
               (120, 30, 20))
    # cyclone spiral
    cx, cy = x + w - 78, y + 52
    for k in range(5):
        s.ring(cx, cy, 12 + k * 7, WHITE, 2)
    s.disc(cx, cy, 5, (255, 240, 200))
    s.line(cx - 40, cy + 34, cx + 40, cy + 30, WHITE, 1)
    s.line(cx - 46, cy + 44, cx + 44, cy + 40, WHITE, 1)
    t.draw(x + 118, y + 8, "BAY OF BENGAL", 10, WHITE, adv=5)
    s.rect(x, y + h - 16, w, 16, (178, 34, 28))
    t.draw(x + 6, y + h - 13, "LANDFALL NOON - 300,000+ OUT", 10, WHITE, adv=5)


def scene_cop(s, t, x, y, w, h):
    s.rect(x, y, w, h, (22, 58, 96))
    s.dither(x, y, w, 10, (30, 70, 110), (22, 58, 96))
    gx, gy, gr = x + 62, y + 52, 34
    s.disc(gx, gy, gr, (64, 140, 110))
    s.poly([(gx - 22, gy - 8), (gx - 6, gy - 16), (gx + 4, gy - 4),
            (gx + 18, gy - 12), (gx + 20, gy + 6), (gx + 2, gy + 12),
            (gx - 14, gy + 14), (gx - 24, gy + 4)], (36, 110, 66))
    s.poly([(gx - 30, gy + 18), (gx - 10, gy + 10), (gx + 8, gy + 22),
            (gx - 4, gy + 30), (gx - 26, gy + 28)], (52, 130, 80))
    s.ring(gx, gy, gr, (200, 220, 235), 2)
    # thermometer
    tx, ty = x + w - 52, y + 16
    s.rect(tx, ty, 10, 56, (200, 200, 200))
    s.rect(tx + 2, ty + 30, 6, 26, RED)
    s.disc(tx + 5, ty + 60, 9, RED)
    s.disc(tx + 5, ty + 60, 4, (255, 180, 160))
    for k, yy in enumerate([ty + 6, ty + 22, ty + 38, ty + 52]):
        s.rect(tx + 10, yy, 6, 2, WHITE)
    s.rect(x, y + h - 34, w, 18, (178, 34, 28))
    t.draw(x + 6, y + h - 31, "ANTALYA - NOV 20", 10, WHITE, adv=5)
    t.draw(x + w - 118, y + h - 31, "COP31 FINAL DAY", 10, (255, 220, 120), adv=5)
    s.rect(x, y + h - 16, w, 16, GOLD)
    t.draw(x + 6, y + h - 13, "$120BN FINANCE GAP", 10, INK, adv=5)


def scene_selloff(s, t, x, y, w, h):
    s.rect(x, y, w, h, (244, 238, 226))
    pts = [(x + 8, y + 10), (x + 40, y + 14), (x + 72, y + 8), (x + 104, y + 22),
           (x + 136, y + 30), (x + 168, y + 38)]
    for a, b in zip(pts, pts[1:]):
        s.line(a[0], a[1], b[0], b[1], RED, 3)
    for px, py in pts:
        s.disc(px, py, 3, RED)
    s.line(x + 8, y + h - 12, x + w - 8, y + h - 12, GREY, 1)
    t.draw(x + 6, y + h - 12, "ASIA", 9, RED, adv=5)
    t.draw(x + w - 52, y + h - 12, "-4.9%", 9, RED, adv=5)


def scene_bepi(s, t, x, y, w, h):
    s.rect(x, y, w, h, (16, 20, 40))
    for dx, dy in [(20, 10), (60, 18), (120, 8), (160, 20), (90, 26), (150, 34)]:
        s.px(x + dx, y + dy, WHITE)
    s.disc(x + 60, y + 26, 15, (196, 188, 170))
    s.disc(x + 55, y + 22, 3, (150, 142, 122))
    s.disc(x + 66, y + 30, 2, (150, 142, 122))
    s.poly([(x + 96, y + 18), (x + 104, y + 22), (x + 128, y + 20),
            (x + 128, y + 30), (x + 104, y + 28), (x + 96, y + 24)], (200, 200, 210))
    s.rect(x + 128, y + 22, 26, 4, GOLD)
    s.rect(x + 154, y + 20, 8, 8, (220, 220, 230))
    t.draw(x + 6, y + h - 12, "ESA / JAXA", 9, WHITE, adv=5)
    t.draw(x + w - 58, y + h - 12, "8 YEARS", 9, (255, 220, 120), adv=5)


def scene_burnham(s, t, x, y, w, h):
    s.rect(x, y, w, h, (232, 228, 214))
    # EU flag
    s.rect(x + 14, y + 8, 34, 22, BLUE)
    for k in range(8):
        a = math.radians(k * 45)
        s.px(x + 31 + 9 * math.cos(a), y + 19 + 7 * math.sin(a), GOLD)
    # UK flag
    s.rect(x + 58, y + 8, 34, 22, (180, 30, 40))
    s.line(x + 58, y + 8, x + 92, y + 30, WHITE, 3)
    s.line(x + 92, y + 8, x + 58, y + 30, WHITE, 3)
    s.line(x + 75, y + 8, x + 75, y + 30, WHITE, 3)
    s.line(x + 58, y + 19, x + 92, y + 19, WHITE, 3)
    # handshake table
    s.rect(x + 104, y + 22, 66, 6, (120, 90, 60))
    s.rect(x + 112, y + 28, 5, 14, (120, 90, 60))
    s.rect(x + 156, y + 28, 5, 14, (120, 90, 60))
    t.draw(x + 6, y + h - 12, "BRUSSELS", 9, INK, adv=5)
    t.draw(x + w - 46, y + h - 12, "RESET", 9, BLUE, adv=5)


def scene_japan(s, t, x, y, w, h):
    s.rect(x, y, w, h, (244, 238, 226))
    bars = [("OCT 25", 18, GREY), ("APR", 22, GREY), ("AUG", 26, GREY),
            ("OCT 26", 32, RED)]
    bx = x + 10
    for lab, bh, c in bars:
        s.rect(bx, y + h - 14 - bh, 30, bh, c)
        bx += 40
    s.line(x + 6, y + h - 14, x + w - 6, y + h - 14, INK, 1)
    t.draw(x + 6, y + h - 12, "CPI 2.2%", 9, RED, adv=5)
    t.draw(x + w - 62, y + h - 12, "BOJ EYED", 9, INK, adv=5)


def scene_china(s, t, x, y, w, h):
    s.rect(x, y, w, h, (244, 238, 226))
    t.draw(x + 8, y + 4, "1-YEAR 3.00%", 10, RED, adv=5)
    t.draw(x + 8, y + 16, "5-YEAR 3.50%", 10, INK, adv=5)
    for i in range(8):
        s.rect(x + 10 + i * 20, y + 26, 14, 8,
               RED if i % 2 == 0 else GREY)
    t.draw(x + 6, y + h - 12, "PBOC", 9, RED, adv=5)
    t.draw(x + w - 44, y + h - 12, "18 MO", 9, INK, adv=5)


def scene_phillips(s, t, x, y, w, h):
    s.rect(x, y, w, h, (28, 110, 70))
    t.draw(x + 8, y + 4, "118", 22, (255, 220, 120), adv=5, bold=True)
    # bat + ball
    s.line(x + 120, y + 10, x + 150, y + 34, (220, 190, 140), 5)
    s.disc(x + 156, y + 38, 4, WHITE)
    s.line(x + 8, y + h - 12, x + w - 8, y + h - 12, (200, 220, 200), 1)
    t.draw(x + 6, y + h - 12, "CENTURIES x3", 9, WHITE, adv=5)


def scene_bukele(s, t, x, y, w, h):
    s.rect(x, y, w, h, (244, 238, 226))
    t.draw(x + 8, y + 2, "2027", 20, BLUE, adv=5, bold=True)
    s.rect(x + 110, y + 8, 56, 30, (200, 200, 205))
    s.rect(x + 122, y + 2, 32, 8, INK)
    s.rect(x + 132, y + 14, 12, 18, WHITE)
    s.line(x + 132, y + 32, x + 144, y + 18, RED, 2)
    t.draw(x + 6, y + h - 12, "FEB VOTE", 9, BLUE, adv=5)


def scene_senegal(s, t, x, y, w, h):
    s.rect(x, y, w, h, (44, 96, 158))
    s.line(x + 6, y + 28, x + w - 6, y + 24, WHITE, 1)
    s.line(x + 6, y + 36, x + w - 6, y + 32, WHITE, 1)
    s.poly([(x + 60, y + 12), (x + 130, y + 12), (x + 118, y + 26),
            (x + 72, y + 26)], (150, 90, 50))
    s.line(x + 95, y + 12, x + 95, y + 2, (200, 200, 200), 2)
    s.rect(x + 95, y + 2, 14, 8, RED)
    t.draw(x + 6, y + h - 12, "YENNE - 4 DEAD", 9, WHITE, adv=5)


def scene_cgil(s, t, x, y, w, h):
    s.rect(x, y, w, h, (244, 238, 226))
    for i, c in enumerate([RED, WHITE, GREEN, WHITE, RED, WHITE, GREEN]):
        s.rect(x + 8 + i * 24, y + 6, 20, 20, c)
    s.rect(x + 20, y + 30, 60, 10, INK)
    s.rect(x + 110, y + 30, 60, 10, INK)
    t.draw(x + 6, y + h - 12, "24-HR STOPPAGE", 9, RED, adv=5)


def scene_anthropic(s, t, x, y, w, h):
    s.rect(x, y, w, h, (244, 238, 226))
    t.draw(x + 8, y + 2, "$97.17", 18, (198, 120, 30), adv=5, bold=True)
    bars = [(x + 20, 26, 10, GREEN), (x + 48, 22, 14, GREEN),
            (x + 76, 26, 10, GREEN), (x + 104, 16, 20, GREEN),
            (x + 132, 10, 26, GREEN)]
    for bx, by, bh, c in bars:
        s.rect(bx, y + by, 16, bh, c)
    s.line(x + 8, y + 40, x + w - 8, y + 40, GREY, 1)
    t.draw(x + 6, y + h - 12, "NASDAQ", 9, INK, adv=5)
    t.draw(x + w - 40, y + h - 12, "+17%", 9, GREEN, adv=5)


SCENES = [scene_kyiv, scene_akvan, scene_cop, scene_selloff, scene_bepi,
          scene_burnham, scene_japan, scene_china, scene_phillips,
          scene_bukele, scene_senegal, scene_cgil, scene_anthropic]


# ---------------------------------------------------------------- map
CONTINENTS = {
    "NA": [(12, 22), (30, 8), (58, 6), (82, 14), (96, 26), (88, 40),
           (70, 48), (58, 66), (44, 84), (30, 78), (18, 60), (8, 40)],
    "SA": [(66, 92), (82, 88), (96, 100), (100, 122), (90, 150), (78, 168),
           (70, 148), (62, 118), (58, 100)],
    "AF": [(150, 78), (168, 66), (190, 62), (208, 74), (212, 92),
           (204, 116), (192, 140), (180, 132), (166, 110), (152, 96)],
    "EU": [(158, 28), (176, 18), (198, 16), (216, 26), (222, 40),
           (208, 48), (190, 44), (172, 52), (158, 44)],
    "AS": [(226, 20), (252, 10), (290, 14), (312, 30), (306, 52),
           (288, 66), (268, 60), (252, 74), (238, 58), (224, 40)],
    "AU": [(272, 128), (292, 122), (308, 132), (304, 148), (284, 150),
           (270, 142)],
}
PINS = {1: (210, 38), 2: (258, 78), 3: (198, 58), 4: (232, 26),
        6: (182, 36), 7: (248, 48), 8: (262, 58), 9: (298, 148),
        10: (62, 92), 11: (168, 100), 12: (176, 52), 13: (52, 48)}


def draw_map(s, t, x, y, w, h):
    s.rect(x, y, w, h, NAVY)
    for name, pts in CONTINENTS.items():
        s.poly([(x + px * w / 330, y + py * h / 190) for px, py in pts],
               (96, 130, 96))
    s.disc(x + 60, y + 150, 3, (200, 220, 235))
    for num, (px, py) in PINS.items():
        mx = x + px * w / 330
        my = y + py * h / 190
        s.disc(mx, my, 8, RED)
        s.ring(mx, my, 8, WHITE, 1)
        t.draw(mx - 3, my - 5, str(num), 10, WHITE, adv=5)
    # space story badge (bottom-right, clear of pins)
    bx, by = x + w - 134, y + h - 26
    s.rect(bx, by, 128, 18, GOLD)
    t.draw(bx + 5, by + 4, "5 - SPACE, MERCURY", 9, INK, adv=5)

# ---------------------------------------------------------------- content
LEADS = [
    ("01 KYIV - WAR", "Russia fires 30 missiles at Kyiv",
     "Seven waves hit energy sites; 3 killed, bridges hit. "
     "(Kyiv Post)"),
    ("02 ODISHA - CYCLONE", "Cyclone Akvan makes landfall in India",
     "300,000+ evacuated near Gopalpur; gusts 110 km/h. "
     "(IMD, The Hindu)"),
    ("03 ANTALYA - CLIMATE", "COP31 deadlocked on final day",
     "Draft drops fossil-fuel phase-out; $120bn gap open. "
     "(UN News)"),
]
CARDS = [
    ("04 SEOUL / TOKYO - MARKETS", "AI sell-off sinks Asia to worst week",
     "Nikkei -4.9%, KOSPI -5.4%, TAIEX -6.8%; SoftBank -16%. (Reuters)"),
    ("05 SPACE - MERCURY", "BepiColombo reaches Mercury",
     "6bn-mile trip ends; orbit insertion Sat. (ESA, BBC)"),
    ("06 BRUSSELS - EUROPE", "Burnham holds first EU-UK reset summit",
     "Costa and von der Leyen host the UK PM. (EU)"),
    ("07 TOKYO - ECONOMY", "Japan inflation hits 2.2%; BoJ hike eyed",
     "Core CPI up from 2.1% in October. (Reuters)"),
    ("08 BEIJING - ECONOMY", "China holds lending rates for 18th month",
     "1-year 3.0%, 5-year 3.5%. (PBOC, Reuters)"),
    ("09 DUNEDIN - CRICKET", "Phillips makes history with 118",
     "First NZ batter with centuries in all formats. (ICC, AP)"),
    ("10 SAN SALVADOR - POLITICS", "Bukele registers for third-term bid",
     "Feb 2027 vote. (AP)"),
    ("11 DAKAR - MIGRATION", "Migrant boat capsizes off Yenne",
     "Dozens missing after the capsize. (Al Jazeera)"),
    ("12 ROME - LABOUR", "Italy's CGIL holds 24-hr general strike",
     "Stoppage across ~100 squares. (CGIL, AFP)"),
    ("13 NEW YORK - MARKETS", "Anthropic ends first day up 17%",
     "Claude maker closes at $97.17, up 17% on $83 offer. (Nasdaq)"),
]
ALSO = [
    ("14", "HORMUZ", "Attacks on 46 ships; Brent $92.50."),
    ("15", "LONDON", "Fiona the hippo dies at 12."),
    ("16", "GAZA", "Aid score improves in talks."),
    ("17", "LONDON", "UK, Norway order naval vessels."),
    ("18", "LOS ANGELES", "Thomas Markle dies at 82."),
    ("19", "JAKARTA", "Asset-forfeiture bill advances."),
    ("20", "DUBLIN", "Border-poll talks resume."),
    ("21", "WASHINGTON", "Supreme Court weighs TPS bid."),
    ("22", "TAIPEI", "Taiwan tracks Russian bombers."),
    ("23", "TURIN", "ATP Finals: Alcaraz through."),
    ("24", "NEW DELHI", "SCO delegation arrives."),
    ("25", "SEOUL", "Impeach bid filed vs minister."),
    ("26", "BEIJING", "LPR held; yuan steady."),
    ("27", "HONG KONG", "Hang Seng down 2%."),
    ("28", "SYDNEY", "ASX falls on AI fears."),
    ("29", "MUMBAI", "Sensex down; rupee slips."),
    ("30", "NUKU'ALOFA", "Tonga drought declared."),
    ("31", "PARIS", "France edge S. Africa 21-19."),
    ("32", "DAKAR", "Budget passed; debt talks."),
    ("33", "DAR ES SALAAM", "Gold exports jump."),
    ("34", "NEW YORK", "UN marks World Children's Day."),
    ("35", "RIYADH", "Houthi claim denied."),
    ("36", "MEXICO CITY", "Revolution Day parade."),
]
FIGURES = [
    ("3", "KYIV WATER WORKERS KILLED", "KYIV POST"),
    ("300,000+", "EVACUATED AHEAD OF AKVAN", "IMD"),
    ("~30", "MISSILES FIRED AT KYIV", "KYIV POST"),
    ("-7%", "ASIA'S WORST WEEK SINCE 2020", "REUTERS"),
    ("2.2%", "JAPAN OCT CPI; BOJ EYED", "REUTERS"),
    ("118", "PHILLIPS' HISTORIC CENTURY", "ICC"),
]
REGIONS = [("EUROPE", 8), ("AMERICAS", 6), ("ASIA-PACIFIC", 11),
           ("MIDEAST", 3), ("AFRICA", 3), ("OCEANIA", 3), ("WORLD", 2)]
DATE_CHECK = ("First reported Thursday 19 Nov, so NOT shown as Friday's "
              "news: the Trump-Xi-Putin Shenzhen summit itself - Anthropic's "
              "$83 IPO pricing - ICJ Myanmar verdict - GTA VI's midnight "
              "launch - the $190.4m Van Gogh sale - Voyager 1's "
              "one-light-day confirmation - the EU's 45bn Ukraine loan - "
              "Han Duck-soo's acquittal - the Crimean Bridge attack - the "
              "Houthi strike on Riyadh's PIF tower.")


def also_item(t, x, y, num, place, text, maxw):
    t.draw(x, y, num, 9, RED, adv=5, bold=True)
    t.draw(x + 20, y, place, 9, INK, adv=5, bold=True)
    pw = t.width(place, 9, 5)
    first_x = x + 20 + pw + 6
    lines = t.wrap(text, 9, maxw - 20 - pw - 6, adv=6)
    yy = y
    for i, ln in enumerate(lines):
        t.draw(first_x if i == 0 else x + 20, yy, ln, 9, INK, adv=6)
        yy += 11
    return yy - y


def build():
    s = Sheet(W, H, PAPER)
    t = Type(s)
    M = 28
    CW = W - 2 * M

    # top strip
    t.draw(M, 8, "THE WORLD IN ONE DAY", 11, INK, adv=5, bold=True)
    right = "FRIDAY'S NEWS - ONE PAGE - 36 STORIES - 7 REGIONS"
    t.draw(M + CW - t.width(right, 11, 5), 8, right, 11, RED, adv=5)
    s.hline(M, 28, CW, INK, 2)

    # masthead
    mast = "Friday 20 November 2026"
    cap = fit_cap(t, mast, CW, 52, adv=6, bold=True)
    t.draw(M, 32, mast, cap, INK, adv=6, bold=True)
    sub = ("Missiles hit Kyiv - Cyclone Akvan comes ashore - "
           "COP31 deadlocked - Asia's AI sell-off")
    sw = t.width(sub, 12, 6)
    t.draw(M + (CW - sw) / 2, 122, sub, 12, RED, adv=6)
    s.hline(M, 142, CW, INK, 2)

    # figures band
    fy = 150
    cell = (CW - 5 * 10) / 6
    for i, (num, cap_text, src) in enumerate(FIGURES):
        cx = M + i * (cell + 10)
        ncap = fit_cap(t, num, cell, 26, adv=5, bold=True)
        t.draw(cx, fy, num, ncap, INK, adv=5, bold=True)
        lines = t.wrap(cap_text, 9, cell, adv=6)
        yy = fy + 30
        for ln in lines[:2]:
            t.draw(cx, yy, ln, 9, GREY, adv=6)
            yy += 11
        t.draw(cx, fy + 52, src, 8, GREY, adv=5)
    s.hline(M, fy + 62, CW, INK, 1)

    # region bar
    ry = 220
    xx = M
    for name, n in REGIONS:
        chip = f"{name} {n}"
        wch = t.width(chip, 10, 5) + 16
        s.rect(xx, ry, wch, 18, NAVY if name != "ASIA-PACIFIC" else RED)
        t.draw(xx + 8, ry + 4, chip, 10, WHITE, adv=5)
        xx += wch + 6
    rtext = "36 STORIES - 7 REGIONS"
    t.draw(M + CW - t.width(rtext, 10, 5), ry + 4, rtext, 10, GREY, adv=5)
    s.hline(M, ry + 24, CW, INK, 1)

    # leads
    ly = 250
    colw = (CW - 2 * 13) / 3
    for i, (kick, head, deck) in enumerate(LEADS):
        x = M + i * (colw + 13)
        SCENES[i](s, t, x, ly, colw, 104)
        yy = ly + 110
        t.draw(x, yy, kick, 9, RED, adv=5, bold=True)
        yy += 14
        for ln in t.wrap(head, 18, colw, adv=5)[:2]:
            t.draw(x, yy, ln, 18, INK, adv=5, bold=True)
            yy += 22
        for ln in t.wrap(deck, 10, colw, adv=6)[:2]:
            t.draw(x, yy, ln, 10, INK, adv=6)
            yy += 13

    # small cards
    cy0 = 452
    cardw = (CW - 4 * 9) / 5
    for row in range(2):
        for col in range(5):
            k = row * 5 + col
            kick, head, deck = CARDS[k]
            x = M + col * (cardw + 9)
            y = cy0 + row * 136
            SCENES[3 + k](s, t, x, y, cardw, 48)
            yy = y + 52
            t.draw(x, yy, kick, 8, RED, adv=5, bold=True)
            yy += 11
            for ln in t.wrap(head, 13, cardw, adv=5)[:2]:
                t.draw(x, yy, ln, 13, INK, adv=5, bold=True)
                yy += 17
            for ln in t.wrap(deck, 9, cardw, adv=6)[:3]:
                t.draw(x, yy, ln, 9, INK, adv=6)
                yy += 12

    # map + also
    my = 730
    t.draw(M, my, "THE WORLD - WHERE IT HAPPENED", 11, INK, adv=5, bold=True)
    t.draw(M, my + 14, "Friday 20 November 2026", 9, GREY, adv=5)
    draw_map(s, t, M, my + 30, 330, 170)
    ax = M + 330 + 24
    acolw = (M + CW - ax - 20) / 2
    t.draw(ax, my, "ALSO ON FRIDAY 20 NOVEMBER - 23 MORE STORIES", 11, INK,
           adv=5, bold=True)
    y1 = my + 18
    y2 = my + 18
    for k, (num, place, text) in enumerate(ALSO):
        if k < 12:
            y1 += also_item(t, ax, y1, num, place, text, acolw) + 2
        else:
            y2 += also_item(t, ax + acolw + 20, y2, num, place, text, acolw) + 2

    # date check
    dy = 938
    s.frame(M, dy - 8, CW, 52, RED, 2)
    t.draw(M + 10, dy - 4, "DATE CHECK", 10, RED, adv=5, bold=True)
    lines = t.wrap(DATE_CHECK, 9, CW - 20, adv=6)
    yy = dy + 10
    for ln in lines[:3]:
        t.draw(M + 10, yy, ln, 9, INK, adv=6)
        yy += 12

    # footer
    foot = ("Every story here happened, or was first reported, on Friday "
            "20 November 2026. Disputed claims are attributed.")
    t.draw(M + (CW - t.width(foot, 9, 6)) / 2, 1006, foot, 9, GREY, adv=6)
    return s


def main():
    s = build()
    s.png(os.path.join(OUT, "entry.png"))


if __name__ == "__main__":
    main()
