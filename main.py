#!/usr/bin/env python3
"""bigpig-news v2: THE WORLD IN ONE DAY, Friday 20 November 2026.

One 1024x1024 PNG, pure Python 3.13 standard library (math, os, struct,
zlib). No third-party packages, no network, no file reads. Deterministic:
two runs write byte-identical files.

Design (fresh rebuild after the v1 autopsy): cream broadsheet, giant date
masthead, one-line subhead, six-figure band, region bar that sums to the
story total, 3 big + 10 small illustrated cards (13, numbered, pins on
the map match), numbered ALSO list, and a DATE CHECK box naming the
Thursday stories deliberately left out. Every lead and card is Friday
20 November 2026 news (any time zone); see NEWS-20261120-v2.md.
"""
import math
import os
import struct
import zlib

W = 1024
H = 1024

CREAM = (246, 238, 220)
CREAM2 = (238, 228, 205)
INK = (24, 24, 28)
NAVY = (26, 42, 74)
NAVY2 = (44, 66, 110)
RED = (178, 34, 52)
RED2 = (140, 22, 38)
GOLD = (198, 148, 44)
TEAL = (18, 96, 96)
GREEN = (34, 112, 58)
GREEN2 = (16, 78, 38)
SKY = (168, 200, 224)
SKY2 = (214, 230, 238)
SAND = (214, 178, 120)
BROWN = (120, 82, 40)
GREY = (120, 118, 110)
LIGHT = (246, 244, 238)
WHITE = (255, 255, 255)

# 5x7 pixel alphabet. '#' is a set pixel, '.' is clear. Lowercase folds
# to uppercase. Anything unlisted prints as a blank.
GLYPHS = {
    'A': ('.###.', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'),
    'B': ('####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'),
    'C': ('.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'),
    'D': ('####.', '#...#', '#...#', '#...#', '#...#', '#...#', '####.'),
    'E': ('#####', '#....', '#....', '####.', '#....', '#....', '#####'),
    'F': ('#####', '#....', '#....', '####.', '#....', '#....', '#....'),
    'G': ('.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'),
    'H': ('#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'),
    'I': ('.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'),
    'J': ('..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'),
    'K': ('#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'),
    'L': ('#....', '#....', '#....', '#....', '#....', '#....', '#####'),
    'M': ('#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'),
    'N': ('#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#', '#...#'),
    'O': ('.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'),
    'P': ('####.', '#...#', '#...#', '####.', '#....', '#....', '#....'),
    'Q': ('.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'),
    'R': ('####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'),
    'S': ('.####', '#....', '#....', '.###.', '....#', '....#', '####.'),
    'T': ('#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'),
    'U': ('#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'),
    'V': ('#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'),
    'W': ('#...#', '#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'),
    'X': ('#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'),
    'Y': ('#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'),
    'Z': ('#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'),
    '0': ('.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'),
    '1': ('..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'),
    '2': ('.###.', '#...#', '....#', '..##.', '.#...', '#....', '#####'),
    '3': ('####.', '....#', '....#', '.###.', '....#', '....#', '####.'),
    '4': ('...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'),
    '5': ('#####', '#....', '####.', '....#', '....#', '#...#', '.###.'),
    '6': ('.###.', '#....', '#....', '####.', '#...#', '#...#', '.###.'),
    '7': ('#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'),
    '8': ('.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'),
    '9': ('.###.', '#...#', '#...#', '.####', '....#', '....#', '.###.'),
    ' ': ('.....', '.....', '.....', '.....', '.....', '.....', '.....'),
    '.': ('.....', '.....', '.....', '.....', '.....', '.##..', '.##..'),
    ',': ('.....', '.....', '.....', '.....', '.##..', '..#..', '.#...'),
    ';': ('.....', '.##..', '.....', '.....', '.##..', '..#..', '.#...'),
    ':': ('.....', '.##..', '.##..', '.....', '.##..', '.##..', '.....'),
    '!': ('..#..', '..#..', '..#..', '..#..', '..#..', '.....', '..#..'),
    '?': ('.###.', '#...#', '....#', '..##.', '..#..', '.....', '..#..'),
    "'": ('..#..', '..#..', '.#...', '.....', '.....', '.....', '.....'),
    '"': ('.#.#.', '.#.#.', '.....', '.....', '.....', '.....', '.....'),
    '-': ('.....', '.....', '.....', '.###.', '.....', '.....', '.....'),
    '/': ('....#', '...#.', '...#.', '..#..', '.#...', '.#...', '#....'),
    '(': ('...#.', '..#..', '..#..', '..#..', '..#..', '..#..', '...#.'),
    ')': ('.#...', '..#..', '..#..', '..#..', '..#..', '..#..', '.#...'),
    '&': ('.##..', '#..#.', '#.#..', '.#...', '#.#.#', '#..#.', '.##.#'),
    '%': ('##..#', '##.#.', '...#.', '..#..', '.#...', '#.##.', '#..##'),
    '$': ('..#..', '.####', '#.#..', '.###.', '..#.#', '####.', '..#..'),
    '#': ('.#.#.', '.#.#.', '#####', '.#.#.', '#####', '.#.#.', '.#.#.'),
    '*': ('.....', '#.#.#', '.###.', '#.#.#', '.....', '.....', '.....'),
    '+': ('.....', '..#..', '..#..', '#####', '..#..', '..#..', '.....'),
    '=': ('.....', '.....', '#####', '.....', '#####', '.....', '.....'),
    '<': ('...#.', '..#..', '.#...', '#....', '.#...', '..#..', '...#.'),
    '>': ('.#...', '..#..', '...#.', '....#', '...#.', '..#..', '.#...'),
    '@': ('.###.', '#...#', '#.###', '#.#.#', '#.##.', '#....', '.###.'),
    '_': ('.....', '.....', '.....', '.....', '.....', '.....', '#####'),
    '·': ('.....', '.....', '.....', '.##..', '.....', '.....', '.....'),
    '’': ('..#..', '..#..', '.#...', '.....', '.....', '.....', '.....'),
    '‘': ('..#..', '..#..', '.#...', '.....', '.....', '.....', '.....'),
    '“': ('.#.#.', '.#.#.', '.....', '.....', '.....', '.....', '.....'),
    '”': ('.#.#.', '.#.#.', '.....', '.....', '.....', '.....', '.....'),
    '–': ('.....', '.....', '.....', '.###.', '.....', '.....', '.....'),
    '—': ('.....', '.....', '.....', '#####', '.....', '.....', '.....'),
}


class Sheet:
    """A flat RGB canvas with a tiny drawing vocabulary."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg) * (w * h)

    def dot(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def box(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.box(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.box(x, y, t, h, c)

    def frame(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def line(self, x0, y0, x1, y1, c):
        dx = x1 - x0
        dy = y1 - y0
        n = max(abs(dx), abs(dy), 1)
        for s in range(n + 1):
            self.dot(x0 + dx * s // n, y0 + dy * s // n, c)

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.dot(xx, yy, c)

    def ring(self, cx, cy, r, c, t=2):
        for a in range(360):
            th = math.radians(a)
            for k in range(t):
                self.dot(int(cx + (r - k) * math.cos(th)),
                         int(cy + (r - k) * math.sin(th)), c)

    def tri(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        lo = min(y0, y1, y2)
        hi = max(y0, y1, y2)
        for yy in range(lo, hi + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by) or yy == hi:
                    xs.append(ax + (bx - ax) * (yy - ay) / (by - ay))
            if len(xs) >= 2:
                for xx in range(int(min(xs)), int(max(xs)) + 1):
                    self.dot(xx, yy, c)

    def poly(self, pts, c):
        for i in range(len(pts)):
            a = pts[i]
            b = pts[(i + 1) % len(pts)]
            self.line(a[0], a[1], b[0], b[1], c)

    def ellipse(self, cx, cy, rx, ry, c):
        for a in range(360):
            th = math.radians(a)
            self.dot(int(cx + rx * math.cos(th)), int(cy + ry * math.sin(th)), c)

    def arc(self, cx, cy, r, a0, a1, c):
        a = a0
        while a <= a1:
            th = math.radians(a)
            self.dot(int(cx + r * math.cos(th)), int(cy + r * math.sin(th)), c)
            a += 2


def tw(text, sc):
    """Pixel width of text at scale sc (5px glyph + 1px gap, scaled)."""
    return len(text) * 6 * sc - sc


def put(s, x, y, text, sc, c, bold=False):
    """Draw text; bold overprints one pixel to the right."""
    cx = x
    for ch in text:
        g = GLYPHS.get(ch.upper(), GLYPHS[' '])
        for r in range(7):
            row = g[r]
            for cc in range(5):
                if row[cc] == '#':
                    for dy in range(sc):
                        for dx in range(sc):
                            s.dot(cx + cc * sc + dx, y + r * sc + dy, c)
                            if bold:
                                s.dot(cx + cc * sc + dx + 1, y + r * sc + dy, c)
        cx += 6 * sc
    return cx


def centre(s, cx, y, text, sc, c, bold=False):
    put(s, cx - tw(text, sc) // 2, y, text, sc, c, bold)


def wrap(text, sc, width):
    words = text.split()
    lines = []
    cur = ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if tw(t, sc) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def block(s, x, y, text, sc, width, c, lh=None, bold=False):
    """Wrapped paragraph; returns the y just below the last line."""
    if lh is None:
        lh = 7 * sc + (3 if sc > 1 else 1)
    yy = y
    for ln in wrap(text, sc, width):
        put(s, x, yy, ln, sc, c, bold)
        yy += lh
    return yy


def write_png(s, path):
    raw = b''
    stride = s.w * 3
    for yy in range(s.h):
        raw += b'\x00' + bytes(s.px[yy * stride:(yy + 1) * stride])

    def chunk(tag, data):
        out = struct.pack('>I', len(data)) + tag + data
        out += struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        return out

    ihdr = struct.pack('>IIBBBBB', s.w, s.h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- data
FIGURES = [
    ('298,676', 'EVACUATED, AKVAN', 'PTI'),
    ('$97.17', 'ANTHROPIC CLOSE, +17%', 'NASDAQ'),
    ('118', 'PHILLIPS, WELLINGTON', 'REUTERS'),
    ('49,097', 'DOW CLOSE', 'NYSE'),
    ('144-80', 'COP31 DRAFT PARAS', 'UNFCCC'),
    ('99', 'GTA 6 METACRITIC', 'METACRITIC'),
]

REGIONS = [('EUROPE', 6, RED), ('AMERICAS', 9, NAVY2),
           ('ASIA-PACIFIC', 8, TEAL), ('MIDEAST', 1, BROWN),
           ('OCEANIA', 5, GREEN), ('WORLD', 7, GOLD)]

# (number, kicker, headline, body, source, scene)
LEADS = [
    (1, 'ODISHA', 'CYCLONE AKVAN COMES ASHORE',
     'Landfall near Gopalpur at noon. 298,676 moved to shelters, 423 '
     'rescue teams out, 69 trains cancelled. Third cyclone here in 24 '
     'days.', 'IMD / PTI', 'akvan'),
    (2, 'ANTALYA', 'COP31: FINAL DAY, NO DEAL YET',
     'The draft is cut from 144 paragraphs to 80. Fossil-fuel language '
     'and the $120bn target are gone. Bowen: we will not leave the '
     'rooms.', 'UN / REUTERS', 'cop31'),
    (3, 'NASDAQ', 'ANTHROPIC CLOSES $97.17, +17%',
     'The record $81bn IPO ends its first day up a sixth, after opening '
     'near $111.50. The market still sold the AI trade.',
     'NASDAQ', 'anthropic'),
]

CARDS = [
    (4, 'MARKETS', 'AI TRADE UNWINDS',
     'Dow 49,097, -2.19%, under 50,000 since June. S&P falls a sixth '
     'day. Nikkei -4.54%.', 'REUTERS', 'markets'),
    (5, 'WELLINGTON', 'PHILLIPS 118, NICHOLLS 146*',
     'New Zealand 317 for 6 at lunch, day two. A 216-run stand after '
     'India had them 70 for 5.', 'REUTERS', 'cricket'),
    (6, 'ANTALYA', 'AI PLEDGE: 9 BACKERS',
     'Turkey asks the summit to back an AI pledge. Nine of nearly 200 '
     'countries sign up.', 'REUTERS', 'copai'),
    (7, 'LEONIDA', 'GTA VI: ALBUM OUT TODAY',
     'Thirty-four tracks land Friday; Miami festival on Saturday. '
     'Day-one sales est. $2bn.', 'DEADLINE', 'gta'),
    (8, 'TOKYO', 'JAPAN CORE CPI +2.2%',
     'Prices rise 2.2% in October, above the 2% target again. A '
     'December rate rise is expected.', 'REUTERS', 'japan'),
    (9, 'LONDON', 'UK CONFIDENCE -22',
     'Shoppers feel better than in October, when sentiment fell to -24. '
     'Still deeply negative.', 'REUTERS', 'uk'),
    (10, 'SANTA CLARA', 'NVIDIA -3.3%',
     'The chipmaker gives back $669bn of value in six trading days as '
     'the AI trade is questioned.', 'IBD', 'nvidia'),
    (11, 'GOA', 'FILM FESTIVAL OPENS',
     'The International Film Festival of India opens in Goa for its '
     '56th edition.', 'PIB', 'iffi'),
    (12, 'DELHI', 'SCO FORUM OPENS',
     'The Shanghai Cooperation Organisation forum opens in Delhi at '
     'noon.', 'ANI', 'sco'),
    (13, 'DEEP SPACE', 'BEPICOLOMBO: 8 YEARS ON',
     'The Mercury probe marks eight years and six billion miles on its '
     'way to the smallest planet.', 'ESA', 'bepi'),
]

ALSO = [
    '14  PANCREATIC-CANCER PILL: 60.7% RESPONSE',
    '15  CANARY ISLANDS: 24,364 ARRIVALS',
    '16  CBO WARNS ON AUKUS COSTS',
    '17  PANGUNA MINE: $370M DEAL',
    '18  UK-EU SUMMIT MEETS AT 10:30',
    '19  MODI MEETS PRINCE AND PRINCESS OF WALES',
    '20  AUSTRALIA SANCTIONS ISRAELI SETTLERS',
    '21  LPG TANKER OFF BULGARIA WAS HIT',
    '22  TAKAICHI SEEKS DIALOGUE WITH CHINA',
    '23  TRUMP PARDONS PETE ROSE, POSTHUMOUSLY',
    '24  CALIFORNIA PROBES NVIDIA ON CHINA CHIPS',
    '25  CANADA COURTS AI DATA CENTRES',
    '26  ADNOC VESSEL ATTACKED IN HORMUZ',
    '27  MUSK AT DEALBOOK: "I AM NOT MAGA"',
    '28  IRISHMAN INDICTED OVER AXE ATTACK',
    '29  NEW FLYING FROG SPECIES IN INDONESIA',
    '30  ROME REBUKES KYIV OVER BLACKLIST',
    '31  SOUTH AUSTRALIA STORM: 24,000 HOMES OUT',
    '32  BITCOIN $61,344, DOWN 26% IN A MONTH',
    '33  XI TO ATTEND G20 IN FLORIDA NEXT MONTH',
    '34  GTA 6: NO 60FPS MODE, EVEN ON PS5 PRO',
    '35  AMD -7.7% ON SHORT-SELLER REPORT',
    '36  MSCI WORLD: LONGEST LOSING RUN SINCE 2023',
]

DATECHECK = [
    'TRUMP-XI-PUTIN TRILATERAL, SHENZHEN',
    'ICJ: MYANMAR GUILTY OF GENOCIDE, 9-6',
    'ANTHROPIC IPO PRICED $83',
    'GTA VI LAUNCH',
    'TRUMP DELAYS IRAN DECISION TO 2027',
    'KYIV EMBASSIES HIT IN DRONE RAID',
    'FIJI DROUGHT DISASTER DECLARED',
    'FIONA THE HIPPO DIES',
    'VOYAGER 1 PASSES ONE LIGHT-DAY (18 NOV)',
    'HAYABUSA2 LANDING ENDS (17 NOV)',
]

# (number, label, x%, y%) on the map panel
PINS = [
    (1, 'AKVAN', 0.74, 0.48), (2, 'COP31', 0.45, 0.28),
    (3, 'ANT', 0.19, 0.26), (4, 'DOW', 0.24, 0.34),
    (5, 'CRICKET', 0.88, 0.82), (6, 'AI PLEDGE', 0.51, 0.42),
    (7, 'GTA VI', 0.27, 0.45), (8, 'CPI', 0.86, 0.34),
    (9, 'GFK', 0.43, 0.18), (10, 'NVIDIA', 0.11, 0.40),
    (11, 'IFFI', 0.68, 0.60), (12, 'SCO', 0.64, 0.40),
    (13, 'BEPICOLOMBO', 0.55, 0.06),
]


def caption(s, x, y, w, text):
    """White caption strip pinned to the bottom of a picture."""
    s.box(x, y, w, 12, INK)
    put(s, x + 4, y + 3, text, 1, LIGHT, bold=True)


def pic_akvan(s, x, y, w, h):
    s.box(x, y, w, h, NAVY)
    cx = x + w // 2
    cy = y + h // 2 - 4
    for r, c in ((34, SKY2), (26, SKY), (18, LIGHT), (10, GOLD)):
        s.ring(cx, cy, r, c, 3)
    s.disc(cx, cy, 5, RED)
    caption(s, x, y + h - 12, w, 'LANDFALL: NOON IST')


def pic_cop31(s, x, y, w, h):
    s.box(x, y, w, h, SKY)
    s.disc(x + int(w * 0.78), y + int(h * 0.26), 11, GOLD)
    s.box(x, y + int(h * 0.62), w, h - int(h * 0.62), GREEN2)
    s.tri([(x + int(w * 0.05), y + h - 12), (x + int(w * 0.30), y + int(h * 0.34)),
           (x + int(w * 0.55), y + h - 12)], GREEN)
    s.box(x + int(w * 0.58), y + int(h * 0.44), int(w * 0.34), int(h * 0.18), NAVY)
    for i in range(4):
        s.box(x + int(w * 0.61) + i * int(w * 0.08), y + int(h * 0.47),
              max(2, int(w * 0.04)), int(h * 0.10), GOLD)
    caption(s, x, y + h - 12, w, 'FINAL DAY - ANTALYA')


def pic_anthropic(s, x, y, w, h):
    s.box(x, y, w, h, (16, 22, 34))
    base = y + h - 18
    tops = [0.62, 0.55, 0.66, 0.48, 0.40, 0.30, 0.20]
    for i, f in enumerate(tops):
        bx = x + 8 + i * int((w - 16) / 7)
        bw = int((w - 16) / 7) - 4
        bh = int((base - y) * f)
        s.box(bx, base - bh, bw, bh, GREEN)
        s.box(bx + bw // 2 - 1, base - bh - 6, 2, 6, GREEN)
    s.line(x + 6, base - int((base - y) * 0.55), x + w - 6,
           base - int((base - y) * 0.22), GOLD)
    caption(s, x, y + h - 12, w, '$97.17 +17%')


def pic_markets(s, x, y, w, h):
    s.box(x, y, w, h, (16, 22, 34))
    base = y + h - 18
    pts = [(x + 6, y + 14), (x + int(w * 0.25), y + 18),
           (x + int(w * 0.45), y + int(h * 0.38)),
           (x + int(w * 0.65), y + int(h * 0.30)),
           (x + int(w * 0.82), y + int(h * 0.62)),
           (x + w - 6, y + h - 22)]
    for a, b in zip(pts, pts[1:]):
        s.line(a[0], a[1], b[0], b[1], RED)
        s.disc(a[0], a[1], 2, RED)
    s.disc(pts[-1][0], pts[-1][1], 2, RED)
    caption(s, x, y + h - 12, w, 'DOW 49,097 -2.19%')


def pic_cricket(s, x, y, w, h):
    s.box(x, y, w, h, GREEN2)
    s.box(x + int(w * 0.30), y + int(h * 0.10), int(w * 0.40),
          int(h * 0.80), (214, 196, 150))
    for i in range(3):
        sx = x + int(w * 0.44) + i * 6
        s.vline(sx, y + int(h * 0.16), int(h * 0.30), GOLD, 3)
    s.disc(x + int(w * 0.78), y + int(h * 0.30), 6, RED)
    s.line(x + int(w * 0.10), y + int(h * 0.72), x + int(w * 0.90),
           y + int(h * 0.72), LIGHT)
    caption(s, x, y + h - 12, w, '118 - 317/6')


def pic_copai(s, x, y, w, h):
    s.box(x, y, w, h, NAVY)
    s.box(x + int(w * 0.34), y + int(h * 0.22), int(w * 0.32),
          int(h * 0.44), NAVY2)
    s.frame(x + int(w * 0.34), y + int(h * 0.22), int(w * 0.32),
            int(h * 0.44), GOLD, 2)
    for i in range(3):
        s.box(x + int(w * 0.38), y + int(h * 0.28) + i * int(h * 0.12),
              int(w * 0.24), 3, GOLD)
    for i in range(3):
        s.disc(x + int(w * 0.20) + i * int(w * 0.30), y + int(h * 0.72), 4, RED)
    caption(s, x, y + h - 12, w, '9 BACKERS')


def pic_gta(s, x, y, w, h):
    s.box(x, y, w, h, (40, 16, 52))
    s.box(x, y + int(h * 0.30), w, int(h * 0.22), (222, 94, 44))
    s.box(x, y + int(h * 0.52), w, int(h * 0.22), (140, 40, 90))
    s.disc(x + int(w * 0.50), y + int(h * 0.34), 9, GOLD)
    s.box(x, y + int(h * 0.74), w, h - int(h * 0.74), (20, 20, 30))
    s.line(x + int(w * 0.72), y + int(h * 0.74), x + int(w * 0.86),
           y + int(h * 0.52), GREEN)
    s.disc(x + int(w * 0.86), y + int(h * 0.50), 4, GREEN)
    put(s, x + 6, y + 6, 'VI', 3, GOLD, bold=True)
    caption(s, x, y + h - 12, w, 'ALBUM OUT TODAY')


def pic_japan(s, x, y, w, h):
    s.box(x, y, w, h, LIGHT)
    s.disc(x + int(w * 0.24), y + int(h * 0.38), 13, RED)
    pts = [(x + int(w * 0.42), y + int(h * 0.62)),
           (x + int(w * 0.58), y + int(h * 0.52)),
           (x + int(w * 0.72), y + int(h * 0.58)),
           (x + int(w * 0.88), y + int(h * 0.34))]
    for a, b in zip(pts, pts[1:]):
        s.line(a[0], a[1], b[0], b[1], NAVY)
        s.disc(a[0], a[1], 2, NAVY)
    s.disc(pts[-1][0], pts[-1][1], 2, NAVY)
    caption(s, x, y + h - 12, w, '+2.2%')


def pic_uk(s, x, y, w, h):
    s.box(x, y, w, h, SKY2)
    s.line(x + int(w * 0.14), y + int(h * 0.22), x + int(w * 0.50),
           y + int(h * 0.55), RED)
    s.line(x + int(w * 0.50), y + int(h * 0.55), x + int(w * 0.86),
           y + int(h * 0.72), RED)
    s.tri([(x + int(w * 0.78), y + int(h * 0.62)),
           (x + int(w * 0.94), y + int(h * 0.62)),
           (x + int(w * 0.86), y + int(h * 0.82))], RED)
    caption(s, x, y + h - 12, w, '-22')


def pic_nvidia(s, x, y, w, h):
    s.box(x, y, w, h, (16, 22, 34))
    s.box(x + int(w * 0.32), y + int(h * 0.24), int(w * 0.36),
          int(h * 0.40), GREEN)
    s.box(x + int(w * 0.38), y + int(h * 0.30), int(w * 0.24),
          int(h * 0.28), (16, 22, 34))
    put(s, x + int(w * 0.44), y + int(h * 0.36), 'N', 1, GREEN, bold=True)
    for i in range(5):
        s.box(x + int(w * 0.20) + i * int(w * 0.12), y + int(h * 0.68),
              max(2, int(w * 0.06)), int(h * 0.06), GOLD)
    caption(s, x, y + h - 12, w, '-3.3%')


def pic_iffi(s, x, y, w, h):
    s.box(x, y, w, h, (20, 20, 30))
    for i in range(5):
        s.box(x + 4 + i * int((w - 8) / 5), y + 6, int((w - 8) / 5) - 3,
              int(h * 0.42), CREAM2)
        s.disc(x + 4 + i * int((w - 8) / 5) + int((w - 8) / 10),
               y + 6 + int(h * 0.21), 4, NAVY)
    s.box(x, y + int(h * 0.58), w, int(h * 0.14), RED)
    caption(s, x, y + h - 12, w, 'GOA')


def pic_sco(s, x, y, w, h):
    s.box(x, y, w, h, SKY)
    s.box(x, y + int(h * 0.66), w, h - int(h * 0.66), (52, 72, 96))
    for i, f in enumerate((0.34, 0.48, 0.38)):
        bh = int(h * f)
        bx = x + int(w * 0.10) + i * int(w * 0.28)
        s.box(bx, y + int(h * 0.66) - bh, int(w * 0.20), bh, NAVY2)
        s.box(bx + 2, y + int(h * 0.66) - bh - 4, int(w * 0.20) - 4, 4, GOLD)
    caption(s, x, y + h - 12, w, 'DELHI')


def pic_bepi(s, x, y, w, h):
    s.box(x, y, w, h, (10, 12, 26))
    for (fx, fy) in ((0.15, 0.20), (0.30, 0.55), (0.55, 0.18), (0.80, 0.45),
                     (0.90, 0.15), (0.42, 0.75)):
        s.disc(x + int(w * fx), y + int(h * fy), 2, LIGHT)
    s.box(x + int(w * 0.40), y + int(h * 0.34), int(w * 0.20),
          int(h * 0.26), GOLD)
    s.box(x + int(w * 0.30), y + int(h * 0.42), int(w * 0.10),
          int(h * 0.10), SKY)
    s.box(x + int(w * 0.60), y + int(h * 0.42), int(w * 0.10),
          int(h * 0.10), SKY)
    s.disc(x + int(w * 0.82), y + int(h * 0.30), 6, (178, 120, 60))
    caption(s, x, y + h - 12, w, '8 YEARS')


PICS = {'akvan': pic_akvan, 'cop31': pic_cop31, 'anthropic': pic_anthropic,
        'markets': pic_markets, 'cricket': pic_cricket, 'copai': pic_copai,
        'gta': pic_gta, 'japan': pic_japan, 'uk': pic_uk,
        'nvidia': pic_nvidia, 'iffi': pic_iffi, 'sco': pic_sco,
        'bepi': pic_bepi}


# ---------------------------------------------------------------- layout
def masthead(s):
    s.box(0, 0, W, 3, RED)
    put(s, 24, 12, 'THE WORLD IN ONE DAY', 2, RED, bold=True)
    r = '36 STORIES - 6 REGIONS - ALL FROM FRIDAY'
    put(s, W - 24 - tw(r, 1), 15, r, 1, INK, bold=True)
    put(s, 24, 32, 'FRIDAY 20 NOVEMBER 2026', 6, NAVY, bold=True)
    put(s, 24, 84,
        "A CYCLONE COMES ASHORE - CLIMATE TALKS REACH THEIR FINAL DAY - "
        "A RECORD IPO'S FIRST CLOSE", 1, RED, bold=True)
    s.hline(24, 100, W - 48, INK, 2)


def figures_band(s, y):
    n = len(FIGURES)
    cw = (W - 48) // n
    for i, (val, lab, src) in enumerate(FIGURES):
        x = 24 + i * cw
        if i:
            s.vline(x - 4, y + 6, 44, GREY, 1)
        centre(s, x + cw // 2, y + 4, val, 3, RED, bold=True)
        centre(s, x + cw // 2, y + 30, lab, 1, NAVY, bold=True)
        centre(s, x + cw // 2, y + 40, src, 1, GREY)
    s.hline(24, y + 52, W - 48, INK, 1)
    return y + 56


def region_bar(s, y):
    x = 24
    for name, count, col in REGIONS:
        label = '%s %d' % (name, count)
        w = tw(label, 1) + 16
        s.box(x, y, w, 20, col)
        put(s, x + 8, y + 7, label, 1, LIGHT, bold=True)
        x += w + 8
    total = 'TOTAL 36 STORIES'
    put(s, W - 24 - tw(total, 1), y + 7, total, 1, INK, bold=True)
    return y + 28


def lead_card(s, num, x, y, w):
    kicker, head, body, src, scene = LEADS[num - 1][1:]
    PICS[scene](s, x, y, w, 84)
    put(s, x, y + 92, '%d' % num, 2, RED, bold=True)
    put(s, x + 20, y + 93, kicker, 1, RED, bold=True)
    yy = block(s, x, y + 112, head, 2, w, NAVY, lh=17, bold=True)
    yy = block(s, x, yy + 4, body, 1, w, INK, lh=9)
    put(s, x, yy + 2, src, 1, GREY, bold=True)


def leads_row(s, y):
    put(s, 24, y, 'TOP STORIES', 2, RED, bold=True)
    s.hline(24, y + 16, W - 48, INK, 1)
    y += 24
    colw = 308
    for i, n in enumerate((1, 2, 3)):
        lead_card(s, n, 24 + i * (colw + 14), y, colw)
    return y + 196


def small_card(s, num, x, y, w):
    kicker, head, body, src, scene = CARDS[num - 4][1:]
    PICS[scene](s, x, y, w, 44)
    put(s, x, y + 50, '%d' % num, 1, RED, bold=True)
    put(s, x + 14, y + 51, kicker, 1, RED, bold=True)
    yy = block(s, x, y + 62, head, 2, w, NAVY, lh=17, bold=True)
    yy = block(s, x, yy + 2, body, 1, w, INK, lh=8)
    put(s, x, yy + 1, src, 1, GREY, bold=True)


def grid_rows(s, y):
    put(s, 24, y, 'MORE OF THE DAY', 2, RED, bold=True)
    s.hline(24, y + 16, W - 48, INK, 1)
    y += 24
    colw = 184
    for row in range(2):
        for col in range(5):
            n = 4 + row * 5 + col
            small_card(s, n, 24 + col * (colw + 14), y, colw)
        y += 132
    return y


def draw_map(s, x, y, w, h):
    s.box(x, y, w, h, NAVY)
    # stylised continents: pale blobs in fixed fractions of the panel
    blobs = [(0.10, 0.18, 0.20, 0.16), (0.34, 0.14, 0.16, 0.22),
             (0.56, 0.24, 0.20, 0.18), (0.74, 0.52, 0.20, 0.22),
             (0.30, 0.62, 0.30, 0.26), (0.08, 0.52, 0.16, 0.20)]
    for fx, fy, fw, fh in blobs:
        s.box(x + int(w * fx), y + int(h * fy), int(w * fw), int(h * fh),
              CREAM2)
    for num, lab, fx, fy in PINS:
        px = x + int(w * fx)
        py = y + int(h * fy)
        s.disc(px, py, 7, RED)
        s.ring(px, py, 8, LIGHT, 1)
        centre(s, px, py - 3, str(num), 1, LIGHT, bold=True)
    s.box(x, y + h - 16, w, 16, INK)
    put(s, x + 6, y + h - 12, 'POSITIONS ARE APPROXIMATE - NUMBERS MATCH '
        'THE 13 STORIES ABOVE', 1, LIGHT)


def also_list(s, x, y, w):
    put(s, x, y, 'ALSO ON FRIDAY 20 NOVEMBER - 23 MORE', 2, RED, bold=True)
    s.hline(x, y + 16, w, INK, 1)
    y += 24
    half = 12
    for col in range(2):
        cx = x + col * (w // 2)
        for i, item in enumerate(ALSO[col * half:(col + 1) * half]):
            put(s, cx, y + i * 12, item, 1, INK)
    return y + half * 12


def datecheck_box(s, y):
    s.frame(24, y, W - 48, 66, RED, 2)
    put(s, 32, y + 7, 'DATE CHECK - LEFT OUT ON PURPOSE: THURSDAY 19 NOV, '
        'NOT FRIDAY', 1, RED, bold=True)
    lines = [
        'TRUMP-XI-PUTIN TRILATERAL, SHENZHEN  -  ICJ: MYANMAR GUILTY OF '
        'GENOCIDE, 9-6  -  ANTHROPIC IPO PRICED $83',
        'GTA VI LAUNCH  -  TRUMP DELAYS IRAN DECISION TO 2027  -  KYIV '
        'EMBASSIES HIT IN DRONE RAID  -  FIJI DROUGHT DECLARED',
        'FIONA THE HIPPO DIES  -  VOYAGER 1 PASSES ONE LIGHT-DAY (18 NOV)  '
        '-  HAYABUSA2 LANDING ENDS (17 NOV)',
    ]
    yy = y + 24
    for ln in lines:
        put(s, 32, yy, ln, 1, INK)
        yy += 13
    return y + 66


def footer(s, y):
    s.hline(24, y, W - 48, INK, 2)
    put(s, 24, y + 8,
        'SOURCES: REUTERS, AP, AFP, BBC, THE HINDU, IMD, UN NEWS, '
        'NASDAQ, CRICBUZZ, PTI, IBD', 1, GREY)
    put(s, 24, y + 19,
        'EVERY STORY HAPPENED OR WAS FIRST REPORTED ON FRIDAY 20 NOVEMBER '
        '2026. DISPUTED CLAIMS ARE ATTRIBUTED. ORIGINAL DRAWINGS.', 1, GREY)
    r = 'COMPILED 20 NOV 2026 - ONE IMAGE, ONE DAY'
    put(s, W - 24 - tw(r, 1), y + 19, r, 1, GREY, bold=True)


def build():
    s = Sheet(W, H, CREAM)
    masthead(s)
    y = figures_band(s, 106)
    y = region_bar(s, y + 4)
    y = leads_row(s, y + 6)
    y = grid_rows(s, y + 4)
    put(s, 24, y + 2, 'WHERE IT HAPPENED', 2, RED, bold=True)
    s.hline(24, y + 18, 420, INK, 1)
    also_list(s, 468, y + 2, W - 48 - 444)
    y += 26
    draw_map(s, 24, y, 420, 148)
    y = y + 148 + 10
    y = datecheck_box(s, y)
    footer(s, y + 8)
    return s


def main():
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    path = os.path.join(out, 'entry.png')
    n = write_png(build(), path)
    print('wrote %s (%d bytes)' % (path, n))


if __name__ == '__main__':
    main()
