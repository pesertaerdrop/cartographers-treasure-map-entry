#!/usr/bin/env python3
"""Isle of Crumbs — a one-day treasure map, drawn fresh by this program.

The program renders a single fictional-island treasure map (1024x1024 PNG)
with nine witty, legible place names, a dotted route to a marked X, a
compass rose, a polite sea monster and a small galleon, in one consistent
parchment-and-ink style. Pure standard library only (the grading sandbox
guarantees no third-party packages), fully deterministic: one fixed seed,
no clock, no network, no input files. Output goes only to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Judge brief it is built for (from competition.yaml): charm first, then
legible labels, then cartographic sense, then craft.
"""

import math
import os
import random
import struct
import zlib

W = H = 1024
SEED = 1749

# ---------------------------------------------------------------- palette
PARCHMENT = (232, 211, 160)   # warm sand / island beach
PARCHMENT_DK = (214, 188, 128)
SEA = (168, 203, 192)         # pale teal sea wash
SEA_DK = (120, 168, 158)
LAND = (158, 183, 106)        # island green interior
LAND_DK = (118, 148, 74)
INK = (74, 50, 32)            # dark brown ink for outlines and labels
INK_SOFT = (110, 84, 56)
RED = (176, 58, 46)           # the X and accents
RED_DK = (140, 40, 30)
BLUE = (74, 128, 158)         # river and lake
GOLD = (201, 149, 52)
WHITE = (250, 244, 228)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 cells, '#' = ink. Uppercase only (labels are set
# in capitals, as on an old chart); digits and chart punctuation included.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of a label at the given glyph scale."""
    return len(text) * 6 * scale - scale


class Canvas:
    """A plain RGB raster with slice-based fills (fast in pure Python)."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def _clip(self, x0, x1):
        return max(0, x0), min(self.w, x1)

    def span(self, y, x0, x1, color):
        """Fill one horizontal run [x0, x1) on row y."""
        if y < 0 or y >= self.h:
            return
        x0, x1 = self._clip(x0, x1)
        if x1 <= x0:
            return
        row = y * self.w * 3
        self.px[row + x0 * 3: row + x1 * 3] = bytes(color) * (x1 - x0)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            self.span(yy, x, x + w, color)

    def disc(self, cx, cy, r, color):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.span(cy + dy, cx - dx, cx + dx + 1, color)

    def ring(self, cx, cy, r, t, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            inner = int(math.sqrt(max(0, (r - t) * (r - t) - dy * dy))) if abs(dy) < r - t else -1
            self.span(cy + dy, cx - dx, cx - inner, color)
            self.span(cy + dy, cx + inner + 1, cx + dx + 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-ry, ry + 1):
            dx = int(rx * math.sqrt(max(0.0, 1.0 - (dy / ry) ** 2)))
            self.span(cy + dy, cx - dx, cx + dx + 1, color)

    def polygon(self, pts, color):
        """Scanline fill of a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.span(y, int(math.ceil(xs[k])), int(math.floor(xs[k + 1])) + 1, color)

    def polyline(self, pts, width, color):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], width, color)

    def line(self, x0, y0, x1, y1, width, color):
        """Thick line as a quad plus round caps."""
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        if length == 0:
            self.disc(x0, y0, width // 2 + 1, color)
            return
        nx, ny = -dy / length * width / 2.0, dx / length * width / 2.0
        quad = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
                (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
        self.polygon([(int(round(px)), int(round(py))) for px, py in quad], color)
        self.disc(x0, y0, width // 2 + 1, color)
        self.disc(x1, y1, width // 2 + 1, color)

    def dashed(self, pts, width, color, dash=10, gap=7):
        """A dashed polyline (the treasure route)."""
        for a, b in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            ux, uy = dx / length, dy / length
            d = 0.0
            while d < length:
                e = min(d + dash, length)
                self.line(int(a[0] + ux * d), int(a[1] + uy * d),
                          int(a[0] + ux * e), int(a[1] + uy * e),
                          width, color)
                d = e + gap

    def arc(self, cx, cy, r, a0, a1, width, color, step=0.12):
        pts = []
        a = a0
        while a <= a1 + 1e-9:
            pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
            a += step
        if pts:
            self.polyline(pts, width, color)

    def text(self, x, y, s, scale, color):
        """Draw an uppercase label; (x, y) is the top-left corner."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for r, row in enumerate(glyph):
                for c, cell in enumerate(row):
                    if cell == "1":
                        self.rect(cx + c * scale, y + r * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

# ------------------------------------------------------------ map pieces

def wobbly_blob(rng, cx, cy, r, bumps=30, wobble=0.16):
    """A closed, organic coastline: radius jittered per angle, smoothed."""
    raw = []
    for i in range(bumps):
        ang = 2 * math.pi * i / bumps
        rad = r * (1 + rng.uniform(-wobble, wobble))
        raw.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang) * 0.92))
    pts = []
    for i in range(len(raw)):
        p0 = raw[i - 1]
        p1 = raw[i]
        p2 = raw[(i + 1) % len(raw)]
        # midpoint smoothing keeps the coast soft, never spiky
        pts.append((int((p0[0] + 2 * p1[0] + p2[0]) / 4),
                    int((p0[1] + 2 * p1[1] + p2[1]) / 4)))
    # subdivide once more so the coast reads as a curve, not a polygon
    smooth = []
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        smooth.append(a)
        smooth.append(((a[0] + b[0]) // 2, (a[1] + b[1]) // 2))
    return smooth


def shrink_toward(pts, cx, cy, factor):
    return [(int(cx + (x - cx) * factor), int(cy + (y - cy) * factor))
            for x, y in pts]


def compass_rose(cv, cx, cy, r):
    """An eight-point rose: long N/E/S/W spikes, short diagonals."""
    cv.ring(cx, cy, r, 3, INK)
    cv.ring(cx, cy, r - 8, 2, INK_SOFT)
    for k in range(8):
        ang = -math.pi / 2 + k * math.pi / 4
        long = (k % 2 == 0)
        tip = r - 12 if long else (r - 12) * 0.55
        base = 14 if long else 9
        bx, by = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
        tx, ty = cx + tip * math.cos(ang), cy + tip * math.sin(ang)
        cv.polygon([(int(tx), int(ty)),
                    (int(cx + bx * base), int(cy + by * base)),
                    (int(cx - bx * base), int(cy - by * base))],
                   INK if long else INK_SOFT)
    cv.disc(cx, cy, 7, RED)
    cv.disc(cx, cy, 3, GOLD)
    cv.text_center(cx, cy - r - 26, "N", 3, INK)
    cv.text_center(cx, cy + r + 8, "S", 3, INK)
    cv.text(cx + r + 10, cy - 10, "E", 3, INK)
    cv.text(cx - r - 26, cy - 10, "W", 3, INK)


def sea_monster(cv, x, y, s):
    """A friendly serpent: three humps, a smiling head, a little spout."""
    humps = [(x, y), (x + 34 * s, y - 8 * s), (x + 68 * s, y),
             (x + 102 * s, y - 6 * s)]
    for hx, hy in humps:
        cv.ellipse(hx, hy, 20 * s, 12 * s, SEA_DK)
        cv.ellipse(hx, hy - 3 * s, 16 * s, 8 * s, (96, 142, 132))
    hx, hy = x + 132 * s, y - 26 * s
    cv.ellipse(hx, hy, 16 * s, 12 * s, SEA_DK)          # head
    cv.polygon([(hx - 4 * s, hy - 10 * s), (hx + 2 * s, hy - 22 * s),
                (hx + 8 * s, hy - 10 * s)], SEA_DK)     # horn
    cv.disc(hx + 6 * s, hy - 3 * s, 3 * s, WHITE)       # eye
    cv.disc(hx + 7 * s, hy - 3 * s, 2 * s, INK)         # pupil
    cv.arc(hx - 2 * s, hy + 2 * s, 7 * s, 0.15, math.pi - 0.4, 2, INK)
    for i, dy in enumerate((0, -8, -16)):
        cv.disc(hx - 6 * s + i * 3 * s, hy - 26 * s + dy, 2 * s, BLUE)
    cv.arc(x - 14 * s, y + 6 * s, 12 * s, 0.2, math.pi - 0.5, 2, SEA_DK)


def galleon(cv, x, y, s):
    """A small three-sail galleon, homeward bound."""
    cv.polygon([(x, y), (x + 96 * s, y), (x + 84 * s, y + 22 * s),
                (x + 12 * s, y + 22 * s)], (122, 74, 44))     # hull
    cv.line(x + 8 * s, y, x + 88 * s, y, 3, INK)
    cv.line(x + 48 * s, y, x + 48 * s, y - 74 * s, 3, INK)     # mast
    cv.polygon([(x + 50 * s, y - 72 * s), (x + 84 * s, y - 56 * s),
                (x + 50 * s, y - 40 * s)], WHITE)              # mainsail
    cv.polygon([(x + 46 * s, y - 72 * s), (x + 16 * s, y - 58 * s),
                (x + 46 * s, y - 44 * s)], WHITE)              # foresail
    cv.polygon([(x + 48 * s, y - 74 * s), (x + 70 * s, y - 68 * s),
                (x + 48 * s, y - 62 * s)], RED)                # flag
    cv.arc(x + 20 * s, y + 30 * s, 16 * s, 0.15, math.pi - 0.2, 2, SEA_DK)
    cv.arc(x + 70 * s, y + 30 * s, 16 * s, 0.15, math.pi - 0.2, 2, SEA_DK)


def palm(cv, x, y, s):
    cv.line(x, y, x + 3 * s, y - 26 * s, 3, (122, 74, 44))
    top = (x + 3 * s, y - 26 * s)
    for ang in (-2.4, -1.8, -1.2, -0.6, 0.0, 0.6):
        ex = top[0] + int(16 * s * math.cos(ang - math.pi / 2))
        ey = top[1] + int(16 * s * math.sin(ang - math.pi / 2)) + 6 * s
        cv.line(top[0], top[1], ex, ey, 2, LAND_DK)
    cv.disc(top[0] - 3 * s, top[1] + 2 * s, 2 * s, (96, 64, 32))
    cv.disc(top[0] + 4 * s, top[1] + 3 * s, 2 * s, (96, 64, 32))


def pine(cv, x, y, s):
    cv.polygon([(x, y - 26 * s), (x - 11 * s, y), (x + 11 * s, y)], LAND_DK)
    cv.polygon([(x, y - 36 * s), (x - 8 * s, y - 14 * s),
                (x + 8 * s, y - 14 * s)], (96, 128, 62))
    cv.line(x, y, x, y + 5 * s, 3, (122, 74, 44))


def hill(cv, x, y, w, h):
    cv.polygon([(x - w, y), (x, y - h), (x + w, y)], PARCHMENT_DK)
    cv.polygon([(x - w // 3, y - h // 3), (x, y - h),
                (x + w // 4, y - h // 4)], WHITE)
    cv.line(x - w, y, x, y - h, 2, INK_SOFT)
    cv.line(x + w, y, x, y - h, 2, INK_SOFT)


def gull(cv, x, y, s):
    cv.arc(x - 6 * s, y, 6 * s, math.pi * 1.15, math.pi * 1.85, 2, INK_SOFT)
    cv.arc(x + 6 * s, y, 6 * s, math.pi * 1.15, math.pi * 1.85, 2, INK_SOFT)


def wave(cv, x, y, s):
    cv.arc(x, y, 10 * s, math.pi * 1.1, math.pi * 1.9, 2, SEA_DK)
    cv.arc(x + 16 * s, y + 2 * s, 8 * s, math.pi * 1.1, math.pi * 1.9, 2, SEA_DK)


def skull(cv, x, y, s):
    cv.disc(x, y, 9 * s, INK)
    cv.rect(x - 6 * s, y + 3 * s, 12 * s, 6 * s, INK)
    cv.disc(x - 3 * s, y - 2 * s, 2 * s, WHITE)
    cv.disc(x + 3 * s, y - 2 * s, 2 * s, WHITE)
    cv.line(x - 12 * s, y + 12 * s, x + 12 * s, y + 12 * s, 2, INK)
    cv.line(x - 12 * s, y + 12 * s, x - 8 * s, y + 9 * s, 2, INK)
    cv.line(x + 12 * s, y + 12 * s, x + 8 * s, y + 9 * s, 2, INK)

# ---------------------------------------------------------------- layout

def vtext(cv, x, y, s, scale, color):
    """Vertical label, reading top to bottom (for the narrow west sea)."""
    cy = y
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[" "])
        for r, row in enumerate(glyph):
            for c, cell in enumerate(row):
                if cell == "1":
                    # 90 deg clockwise: glyph row becomes x, mirrored
                    cv.rect(x + (6 - r) * scale, cy + c * scale,
                            scale, scale, color)
        cy += 6 * scale


def leader(cv, x0, y0, x1, y1):
    cv.dashed([(x0, y0), (x1, y1)], 2, INK_SOFT, dash=5, gap=5)
    cv.disc(x1, y1, 4, RED)


def draw_map():
    rng = random.Random(SEED)
    cv = Canvas(W, H, SEA)

    # --- parchment stains and speckles in the sea (texture, deterministic)
    for _ in range(5):
        sx = rng.randint(60, W - 60)
        sy = rng.randint(60, H - 60)
        cv.ellipse(sx, sy, rng.randint(35, 80), rng.randint(22, 55),
                   (162, 196, 184))
    for _ in range(1100):
        x = rng.randint(30, W - 30)
        y = rng.randint(30, H - 30)
        cv.rect(x, y, 2, 2, (140, 178, 166) if rng.random() < 0.5
                else (188, 214, 202))

    # --- sea furniture
    for (x, y) in [(150, 450), (120, 600), (880, 450), (905, 650),
                   (950, 850), (60, 350), (920, 250), (60, 760)]:
        wave(cv, x, y, 1)
    for (x, y) in [(250, 160), (285, 200), (90, 300), (905, 300), (935, 700)]:
        gull(cv, x, y, 1)
    compass_rose(cv, 845, 178, 62)
    galleon(cv, 105, 175, 1)
    sea_monster(cv, 120, 862, 1)

    # --- the island
    coast = wobbly_blob(rng, 500, 560, 270)
    cv.polygon(coast, PARCHMENT)
    cv.polyline(coast + [coast[0]], 4, INK)
    inner = shrink_toward(coast, 500, 560, 0.86)
    cv.polygon(inner, LAND)
    cv.polyline(inner + [inner[0]], 2, INK_SOFT)
    # a bay bitten out of the west coast (notch + inner shoreline)
    cv.ellipse(245, 645, 46, 46, SEA)
    cv.arc(245, 645, 46, -math.pi * 0.5, math.pi * 0.5, 3, INK)

    # --- interior: lake, river, hills, forest, palms, gulch, shoals
    cv.ellipse(430, 520, 55, 34, BLUE)
    cv.ellipse(430, 520, 55, 34, BLUE)
    cv.polyline([(392, 530), (345, 565), (300, 600), (255, 632)],
                7, BLUE)
    cv.polyline([(392, 530), (345, 565), (300, 600), (255, 632)],
                3, (120, 170, 195))
    hill(cv, 560, 500, 72, 56)          # Mt. Sneeze
    hill(cv, 380, 650, 55, 40)
    for (x, y) in [(330, 470), (360, 500), (320, 510), (385, 470),
                   (350, 530), (405, 505)]:
        pine(cv, x, y, 1)               # the Giggling Grove
    for (x, y) in [(425, 700), (460, 715), (400, 722)]:
        palm(cv, x, y, 1)               # the Weeping Palms
    cv.polyline([(545, 640), (575, 665), (560, 690), (595, 712)], 3, INK_SOFT)
    cv.polyline([(565, 632), (595, 658), (580, 684), (615, 706)], 3, INK_SOFT)
    for (x, y) in [(820, 800), (845, 815), (795, 822), (860, 790)]:
        cv.arc(x, y, 12, 0.2, math.pi - 0.3, 2, SEA_DK)   # Snailshell Shoals

    # --- the route: landing cove to the X (kept clear of the lake and labels)
    route = [(500, 800), (520, 730), (470, 670), (430, 600),
             (500, 540), (570, 480), (630, 455), (700, 430)]
    cv.dashed(route, 4, RED_DK, dash=11, gap=8)
    for (x, y) in route[1:-1]:
        cv.disc(x, y, 3, RED_DK)
    x_x, x_y = 700, 430
    cv.ring(x_x, x_y, 26, 3, RED)
    cv.line(x_x - 18, x_y - 18, x_x + 18, x_y + 18, 7, RED)
    cv.line(x_x - 18, x_y + 18, x_x + 18, x_y - 18, 7, RED)

    # --- title cartouche
    cv.rect(300, 44, 424, 74, PARCHMENT)
    for (rx, ry, rw, rh, wdt) in [(300, 44, 424, 74, 4), (308, 52, 408, 58, 2)]:
        cv.line(rx, ry, rx + rw, ry, wdt, INK)
        cv.line(rx, ry + rh, rx + rw, ry + rh, wdt, INK)
        cv.line(rx, ry, rx, ry + rh, wdt, INK)
        cv.line(rx + rw, ry, rx + rw, ry + rh, wdt, INK)
    skull(cv, 330, 76, 1)
    cv.text_center(524, 58, "ISLE OF CRUMBS", 4, INK)
    cv.text_center(524, 94, "SURVEY'D BY CAP'N WOBBLE, 1749", 2, INK_SOFT)

    # --- labels (nine places, all legible, each on its own feature)
    cv.text(200, 385, "THE GIGGLING GROVE", 3, INK)
    leader(cv, 350, 410, 338, 452)
    cv.text(470, 420, "MT. SNEEZE", 3, INK)
    leader(cv, 545, 442, 558, 446)
    vtext(cv, 66, 600, "SOGGY BAY", 3, INK)
    leader(cv, 92, 640, 180, 645)
    cv.text(640, 915, "SNAILSHELL SHOALS", 3, INK)
    leader(cv, 790, 912, 815, 825)
    cv.text(300, 745, "THE WEEPING", 3, INK)
    cv.text(300, 769, "PALMS", 3, INK)
    leader(cv, 420, 772, 420, 720)
    cv.text(570, 690, "GULLIBLE", 3, INK)
    cv.text(570, 714, "GULCH", 3, INK)
    leader(cv, 600, 690, 588, 668)
    cv.text(760, 380, "CAP'N CRUMB'S", 3, INK)
    cv.text(760, 404, "CACHE", 3, INK)
    leader(cv, 760, 392, 722, 420)
    cv.text(620, 505, "X MARKS", 3, INK)
    cv.text(620, 529, "THE SPOT", 3, INK)
    leader(cv, 750, 517, 712, 458)
    cv.text(300, 915, "PORT O' PICKLES", 3, INK)
    leader(cv, 500, 912, 500, 812)

    # --- small jokes and chart furniture
    cv.text(205, 545, "YE OLDE SNACK SHACK", 2, INK_SOFT)
    cv.text(40, 800, "HERE BE A VERY", 2, INK)
    cv.text(40, 824, "POLITE KRAKEN", 2, INK)
    cv.text(60, 928, "LEAGUES, APPROXISH", 2, INK)
    for i, col in enumerate((INK, PARCHMENT, INK, PARCHMENT, INK)):
        cv.rect(60 + i * 32, 950, 32, 8, col)
    cv.line(60, 950, 220, 950, 2, INK)
    cv.line(60, 958, 220, 958, 2, INK)

    # --- double-ruled border with corner rosettes
    for (bx, by, bw, bh, wdt) in [(16, 16, 992, 992, 4), (28, 28, 968, 968, 2)]:
        cv.line(bx, by, bx + bw, by, wdt, INK)
        cv.line(bx, by + bh, bx + bw, by + bh, wdt, INK)
        cv.line(bx, by, bx, by + bh, wdt, INK)
        cv.line(bx + bw, by, bx + bw, by + bh, wdt, INK)
    for (cx, cy) in [(16, 16), (1008, 16), (16, 1008), (1008, 1008)]:
        cv.disc(cx, cy, 8, GOLD)
        cv.disc(cx, cy, 4, RED)
    return cv


def write_png(cv, path):
    """Encode the canvas as a plain 8-bit RGB PNG (zlib, filter 0)."""
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    cv = draw_map()
    size = write_png(cv, path)
    print(f"wrote {path} ({cv.w}x{cv.h}, {size} bytes)")
    assert size <= 1048576, "entry.png exceeds the 1 MiB gate"
    assert cv.w <= 1024 and cv.h <= 1024, "entry.png exceeds 1024x1024"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
