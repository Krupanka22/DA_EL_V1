#!/usr/bin/env python3
"""
railway_monitor.py  —  Railway Block Monitor
=============================================
Single-file Python GUI using pygame.
No browser needed. Runs fullscreen on the 3.5" TFT (480×320).

Requirements:
    pip3 install pygame pyserial --break-system-packages

Run:
    python3 railway_monitor.py

Serial ports:
    Nano1 (B1-B4)  → /dev/ttyUSB0
    Nano2 (B5-B11) → /dev/ttyUSB1

Arduino message format:
    N1:B1:OCC   or   N1:B1:CLR
    N2:B7:OCC   etc.
"""

import threading
import time
import logging
import sys
import os

import serial
import pygame

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════
PORT_NANO1   = "/dev/ttyUSB0"
PORT_NANO2   = "/dev/ttyUSB1"
BAUD         = 9600

SCREEN_W     = 480
SCREEN_H     = 320
FPS          = 30
FULLSCREEN   = True          # set False for windowed testing on desktop

# ══════════════════════════════════════════════════════════════════
# COLOURS
# ══════════════════════════════════════════════════════════════════
C_BG         = (13,  17,  23)
C_SURFACE    = (22,  27,  34)
C_BORDER     = (33,  38,  45)
C_TRACK      = (48,  54,  61)
C_TEXT       = (230, 237, 243)
C_MUTED      = (72,  79,  88)
C_GREEN      = (46,  160,  67)
C_GREEN_HI   = (63,  185,  80)
C_RED        = (218,  54,  51)
C_RED_HI     = (248,  81,  73)
C_YELLOW     = (210, 153,  34)
C_WHITE      = (255, 255, 255)
C_NANO_ON    = (63,  185,  80)
C_NANO_OFF   = (72,  79,  88)

# ══════════════════════════════════════════════════════════════════
# SHARED BLOCK STATE
# ══════════════════════════════════════════════════════════════════
BLOCKS       = {f"B{i}": False for i in range(1, 12)}   # False = clear
state_lock   = threading.Lock()
nano_online  = {"1": False, "2": False}

# ══════════════════════════════════════════════════════════════════
# SERIAL READER  (runs in background thread)
# ══════════════════════════════════════════════════════════════════
def serial_reader(port, nano_id):
    while True:
        try:
            log.info(f"NANO{nano_id}: connecting on {port}")
            with serial.Serial(port, BAUD, timeout=2) as ser:
                time.sleep(2)
                ser.reset_input_buffer()
                nano_online[nano_id] = True
                log.info(f"NANO{nano_id}: connected")

                while True:
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        log.info(f"NANO{nano_id} RX: {line!r}")
                        parse_msg(line, nano_id)

        except serial.SerialException as e:
            nano_online[nano_id] = False
            log.error(f"NANO{nano_id}: {e} — retry in 5s")
            time.sleep(5)
        except Exception as e:
            nano_online[nano_id] = False
            log.error(f"NANO{nano_id}: unexpected — {e}")
            time.sleep(5)

def parse_msg(line, nano_id):
    parts = line.split(":")
    if len(parts) != 3:
        return
    _, block, state = parts
    block = block.strip().upper()
    state = state.strip().upper()
    if state == "OK":         # READY handshake
        return
    if block not in BLOCKS:
        return
    if state not in ("OCC", "CLR"):
        return
    with state_lock:
        BLOCKS[block] = (state == "OCC")

# ══════════════════════════════════════════════════════════════════
# TRACK LAYOUT  (all coords for 480×320)
# ══════════════════════════════════════════════════════════════════
#
#  Line C (top)    y=90  :  B8  B9  B10  |merge|  B11
#  Line B (middle) y=165 :  B5  B6  B7  ──╮
#                                           ╰──→ merges into C at x≈335
#  Line A (bottom) y=240 :  B1  B2  B3  B4
#
# Block rect: 50×22 px, centred on track y

TRACK_A_Y    = 240
TRACK_B_Y    = 165
TRACK_C_Y    = 90
MERGE_X      = 335      # x where Line B curves up to join Line C

BLK_W        = 50
BLK_H        = 22

# (block_id, centre_x, centre_y)
BLOCK_LAYOUT = [
    ("B1",   72,  TRACK_A_Y),
    ("B2",  172,  TRACK_A_Y),
    ("B3",  295,  TRACK_A_Y),
    ("B4",  408,  TRACK_A_Y),
    ("B5",   72,  TRACK_B_Y),
    ("B6",  172,  TRACK_B_Y),
    ("B7",  280,  TRACK_B_Y),
    ("B8",   72,  TRACK_C_Y),
    ("B9",  172,  TRACK_C_Y),
    ("B10", 280,  TRACK_C_Y),
    ("B11", 415,  TRACK_C_Y),
]

# ══════════════════════════════════════════════════════════════════
# DRAW HELPERS
# ══════════════════════════════════════════════════════════════════
def draw_rounded_rect(surf, colour, rect, radius=5):
    pygame.draw.rect(surf, colour, rect, border_radius=radius)

def draw_track(surf):
    """Draw the three-line track layout."""
    lw = 5   # rail line width

    # ── Line A  (bottom straight) ──────────────────────────────
    pygame.draw.line(surf, C_TRACK, (18, TRACK_A_Y), (462, TRACK_A_Y), lw)

    # ── Line C  (top, left segment before merge) ───────────────
    pygame.draw.line(surf, C_TRACK, (18, TRACK_C_Y), (MERGE_X, TRACK_C_Y), lw)

    # ── Line B  (middle, then curves up to C) ──────────────────
    pygame.draw.line(surf, C_TRACK, (18, TRACK_B_Y), (MERGE_X, TRACK_B_Y), lw)

    # Bezier curve: B merges up into C
    # We approximate with a series of short line segments
    steps = 40
    for i in range(steps):
        t0 = i       / steps
        t1 = (i + 1) / steps
        x0 = int(MERGE_X + t0 * (462 - MERGE_X))
        y0 = int(TRACK_B_Y + (TRACK_C_Y - TRACK_B_Y) * (3*t0**2 - 2*t0**3))
        x1 = int(MERGE_X + t1 * (462 - MERGE_X))
        y1 = int(TRACK_B_Y + (TRACK_C_Y - TRACK_B_Y) * (3*t1**2 - 2*t1**3))
        pygame.draw.line(surf, C_TRACK, (x0, y0), (x1, y1), lw)

    # ── End ticks ──────────────────────────────────────────────
    for y in (TRACK_A_Y, TRACK_B_Y, TRACK_C_Y):
        pygame.draw.line(surf, C_TRACK, (18, y-8), (18, y+8), 3)
    pygame.draw.line(surf, C_TRACK, (462, TRACK_A_Y-8), (462, TRACK_A_Y+8), 3)
    pygame.draw.line(surf, C_TRACK, (462, TRACK_C_Y-8), (462, TRACK_C_Y+8), 3)


def draw_merge_zone(surf, font_tiny):
    """Dashed rectangle around the merge region."""
    rect = pygame.Rect(MERGE_X - 2, TRACK_C_Y - 14, 130, TRACK_B_Y - TRACK_C_Y + 28)
    # Draw dashed border manually
    dash = 5
    gap  = 4
    x, y, w, h = rect
    for side in range(4):
        if side == 0:   pts = [(x+i, y)   for i in range(0, w, dash+gap)]
        elif side == 1: pts = [(x+w, y+i) for i in range(0, h, dash+gap)]
        elif side == 2: pts = [(x+w-i, y+h) for i in range(0, w, dash+gap)]
        else:           pts = [(x, y+h-i) for i in range(0, h, dash+gap)]
        for p in pts:
            end = (min(p[0]+dash, x+w) if side in (0,2) else p[0],
                   min(p[1]+dash, y+h) if side in (1,3) else p[1])
            pygame.draw.line(surf, C_YELLOW, p, end, 1)

    lbl = font_tiny.render("MERGE", True, C_YELLOW)
    surf.blit(lbl, (MERGE_X + 35, TRACK_B_Y + 16))


def draw_blocks(surf, font_blk, pulse_alpha):
    """Draw all 11 blocks with current colour."""
    with state_lock:
        snap = dict(BLOCKS)

    for (bid, cx, cy) in BLOCK_LAYOUT:
        occupied = snap[bid]
        bx = cx - BLK_W // 2
        by = cy - BLK_H // 2

        if occupied:
            # Pulse effect: vary brightness
            r = int(C_RED[0] + (C_RED_HI[0] - C_RED[0]) * pulse_alpha)
            g = int(C_RED[1] + (C_RED_HI[1] - C_RED[1]) * pulse_alpha)
            b = int(C_RED[2] + (C_RED_HI[2] - C_RED[2]) * pulse_alpha)
            colour = (r, g, b)
            # Glow shadow
            glow = pygame.Surface((BLK_W + 14, BLK_H + 14), pygame.SRCALPHA)
            glow_c = (*C_RED_HI, int(60 * pulse_alpha + 20))
            pygame.draw.rect(glow, glow_c,
                             (0, 0, BLK_W + 14, BLK_H + 14), border_radius=8)
            surf.blit(glow, (bx - 7, by - 7))
        else:
            colour = C_GREEN

        draw_rounded_rect(surf, colour, pygame.Rect(bx, by, BLK_W, BLK_H), 4)

        # Label
        num = bid[1:]   # "1" from "B1"
        label = f"BLK {num}" if len(num) == 1 else f"BLK{num}"
        txt = font_blk.render(label, True, C_WHITE)
        txt_r = txt.get_rect(center=(cx, cy))
        surf.blit(txt, txt_r)


def draw_header(surf, font_hdr, font_small, pulse_alpha):
    """Top bar: title + NANO pills."""
    pygame.draw.rect(surf, C_SURFACE, (0, 0, SCREEN_W, 30))
    pygame.draw.line(surf, C_BORDER, (0, 30), (SCREEN_W, 30), 1)

    title = font_hdr.render("RAILWAY BLOCK MONITOR", True, C_TEXT)
    surf.blit(title, (10, 8))

    # NANO pills
    for idx, nano_id in enumerate(["1", "2"]):
        online = nano_online[nano_id]
        colour = C_NANO_ON if online else C_NANO_OFF
        lbl    = f"NANO-{nano_id}"
        tw     = font_small.size(lbl)[0]
        px     = SCREEN_W - 100 + idx * 52
        py     = 7
        pw     = tw + 14
        ph     = 16
        pygame.draw.rect(surf, C_SURFACE, (px, py, pw, ph), border_radius=8)
        pygame.draw.rect(surf, colour,    (px, py, pw, ph), 1, border_radius=8)
        t = font_small.render(lbl, True, colour)
        surf.blit(t, (px + 7, py + 2))

        # online dot
        dot_colour = (C_GREEN_HI if online else C_MUTED)
        pygame.draw.circle(surf, dot_colour, (px - 6, py + 8), 3)


def draw_line_labels(surf, font_small):
    """A / B / C labels on left edge."""
    for label, y in [("A", TRACK_A_Y), ("B", TRACK_B_Y), ("C", TRACK_C_Y)]:
        t = font_small.render(label, True, C_MUTED)
        surf.blit(t, (6, y - 5))


def draw_statusbar(surf, font_small):
    """Bottom bar: OCC count / CLR count / time."""
    bar_y = SCREEN_H - 22
    pygame.draw.rect(surf, C_SURFACE, (0, bar_y, SCREEN_W, 22))
    pygame.draw.line(surf, C_BORDER, (0, bar_y), (SCREEN_W, bar_y), 1)

    with state_lock:
        occ = sum(1 for v in BLOCKS.values() if v)
    clr = 11 - occ

    occ_t = font_small.render(f"OCC: {occ}", True, C_RED_HI)
    clr_t = font_small.render(f"CLR: {clr}", True, C_GREEN_HI)
    ts_t  = font_small.render(time.strftime("%H:%M:%S"), True, C_MUTED)

    surf.blit(occ_t, (10,  bar_y + 4))
    surf.blit(clr_t, (90,  bar_y + 4))
    surf.blit(ts_t,  (SCREEN_W - ts_t.get_width() - 10, bar_y + 4))


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    # ── Start serial threads ────────────────────────────────────
    threading.Thread(target=serial_reader, args=(PORT_NANO1, "1"),
                     daemon=True, name="nano1").start()
    threading.Thread(target=serial_reader, args=(PORT_NANO2, "2"),
                     daemon=True, name="nano2").start()

    # ── pygame init ─────────────────────────────────────────────
    pygame.init()
    pygame.mouse.set_visible(False)

    flags = pygame.FULLSCREEN | pygame.NOFRAME if FULLSCREEN else 0
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption("Railway Monitor")
    clock = pygame.time.Clock()

    # ── Fonts  (use default pygame font, no external fonts needed)
    font_hdr   = pygame.font.SysFont("monospace", 11, bold=True)
    font_small = pygame.font.SysFont("monospace",  9, bold=True)
    font_blk   = pygame.font.SysFont("monospace",  9, bold=True)
    font_tiny  = pygame.font.SysFont("monospace",  8)

    # ── Pulse timer ─────────────────────────────────────────────
    pulse_t = 0.0

    log.info("Display running. Press ESC or Q to quit.")

    while True:
        dt = clock.tick(FPS) / 1000.0   # seconds since last frame
        pulse_t += dt

        # Smooth 0→1→0 pulse for red blocks
        pulse_alpha = (1 + __import__("math").sin(pulse_t * 4)) / 2

        # ── Events ──────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit(); sys.exit()

        # ── Draw ────────────────────────────────────────────────
        screen.fill(C_BG)

        # dot grid background
        for gx in range(0, SCREEN_W, 18):
            for gy in range(30, SCREEN_H - 22, 18):
                pygame.draw.circle(screen, C_BORDER, (gx, gy), 1)

        draw_track(screen)
        draw_merge_zone(screen, font_tiny)
        draw_line_labels(screen, font_small)
        draw_blocks(screen, font_blk, pulse_alpha)
        draw_header(screen, font_hdr, font_small, pulse_alpha)
        draw_statusbar(screen, font_small)

        pygame.display.flip()


if __name__ == "__main__":
    main()