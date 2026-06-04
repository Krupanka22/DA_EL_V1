#!/usr/bin/env python3
"""
railway_monitor.py  —  RCAS: Railway Collision Avoidance System
================================================================
DAA ELC Project  |  Design and Analysis of Algorithms

ALGORITHM:
    A fixed-size Hash Table is maintained per railway line (A, B, C).
    Each sensor that reports OCCUPIED inserts its ID into the table
    under the key "OCCUPIED".  Because all occupied sensors hash to
    the same bucket, the second insertion causes a HASH COLLISION.
    That collision is the algorithmic signal for a COLLISION ALERT.

    Hash Function  :  h(key) = sum(ord(c) for c in key) % TABLE_SIZE
    Collision Res. :  Separate Chaining  (linked list per bucket)
    Alert Condition:  chain_length( h("OCCUPIED") ) >= 2  on any line

    Time Complexity :
        Insert   -> O(1) average
        Lookup   -> O(1) average, O(n) worst case
        Alert    -> O(1)  -- just check chain length

Hardware:
    Nano1 (/dev/ttyUSB0)  ->  Blocks B1-B4   (Line A)
    Nano2 (/dev/ttyUSB1)  ->  Blocks B5-B7   (Line B) + B8-B11 (Line C)

    IR sensor OUT is ACTIVE LOW (LOW = object present).
    Message format:   N1:B1:OCC  |  N1:B1:CLR
"""

import threading
import time
import math
import sys
import logging
import serial
import pygame

# -- Logging -----------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ================================================================
# CONFIG
# ================================================================
PORT_NANO1  = "/dev/ttyUSB0"
PORT_NANO2  = "/dev/ttyUSB1"
BAUD        = 9600
FULLSCREEN  = True          # set False for desktop testing

SCREEN_W    = 480
SCREEN_H    = 320
FPS         = 30

# ================================================================
# COLOURS
# ================================================================
C_BG        = (13,  17,  23)
C_SURFACE   = (22,  27,  34)
C_BORDER    = (33,  38,  45)
C_TRACK     = (48,  54,  61)
C_TEXT      = (230, 237, 243)
C_MUTED     = (72,  79,  88)
C_GREEN     = (46,  160,  67)
C_GREEN_HI  = (63,  185,  80)
C_RED       = (218,  54,  51)
C_RED_HI    = (248,  81,  73)
C_YELLOW    = (210, 153,  34)
C_WHITE     = (255, 255, 255)

# ================================================================
# HASH TABLE  (Separate Chaining)
# ================================================================
class HashTable:
    """
    Fixed-size hash table using separate chaining.

    Hash function : h(key) = sum(ord(c) for c in key) % table_size

    In RCAS:
        key   = "OCCUPIED"  (all occupied sensors hash to same bucket)
        value = block ID  e.g. "B1"
        ALERT = chain length at h("OCCUPIED") >= 2
    """

    def __init__(self, size: int):
        self.size    = size
        self.buckets = [[] for _ in range(size)]

    def _hash(self, key: str) -> int:
        return sum(ord(c) for c in key) % self.size

    def insert(self, key: str, value: str):
        idx = self._hash(key)
        if value not in self.buckets[idx]:
            self.buckets[idx].append(value)

    def remove(self, key: str, value: str):
        idx = self._hash(key)
        try:
            self.buckets[idx].remove(value)
        except ValueError:
            pass

    def get_chain(self, key: str) -> list:
        return list(self.buckets[self._hash(key)])

    def chain_length(self, key: str) -> int:
        return len(self.get_chain(key))

    def debug_str(self) -> str:
        lines = []
        for i, chain in enumerate(self.buckets):
            if chain:
                lines.append(f"  bucket[{i}] -> {chain}")
        return "\n".join(lines) if lines else "  (empty)"


# ================================================================
# LINE SENSOR  (one per railway line)
# ================================================================
class LineSensor:
    def __init__(self, line_id: str, block_ids: list):
        self.line_id   = line_id
        self.block_ids = block_ids
        self.table     = HashTable(size=len(block_ids))
        self._lock     = threading.Lock()

    def update(self, block_id: str, occupied: bool):
        with self._lock:
            if occupied:
                self.table.insert("OCCUPIED", block_id)
                self.table.remove("CLEAR",    block_id)
            else:
                self.table.remove("OCCUPIED", block_id)
                self.table.insert("CLEAR",    block_id)
        log.info(
            f"Line {self.line_id} | {block_id} -> "
            f"{'OCC' if occupied else 'CLR'} | "
            f"occupied={self.occupied_blocks()} | alert={self.alert()}"
        )

    def occupied_blocks(self) -> list:
        with self._lock:
            return self.table.get_chain("OCCUPIED")

    def alert(self) -> bool:
        """Two or more trains on same line = ALERT."""
        with self._lock:
            return self.table.chain_length("OCCUPIED") >= 2


# ================================================================
# GLOBAL STATE
# ================================================================
BLOCKS     = {f"B{i}": False for i in range(1, 12)}
state_lock = threading.Lock()

LINE_A = LineSensor("A", ["B1","B2","B3","B4"])
LINE_B = LineSensor("B", ["B5","B6","B7"])
LINE_C = LineSensor("C", ["B8","B9","B10","B11"])

BLOCK_TO_LINE = {
    "B1": LINE_A, "B2": LINE_A, "B3": LINE_A, "B4": LINE_A,
    "B5": LINE_B, "B6": LINE_B, "B7": LINE_B,
    "B8": LINE_C, "B9": LINE_C, "B10": LINE_C, "B11": LINE_C,
}

nano_online = {"1": False, "2": False}

alert_log  = []
alert_lock = threading.Lock()
MAX_LOG    = 5

def push_alert(msg: str):
    with alert_lock:
        alert_log.insert(0, f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(alert_log) > MAX_LOG:
            alert_log.pop()

# ================================================================
# SERIAL  (background threads)
# ================================================================
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
                        parse_msg(line)
        except serial.SerialException as e:
            nano_online[nano_id] = False
            log.error(f"NANO{nano_id}: {e} -- retry in 5s")
            time.sleep(5)
        except Exception as e:
            nano_online[nano_id] = False
            log.error(f"NANO{nano_id}: unexpected -- {e}")
            time.sleep(5)

def parse_msg(line: str):
    parts = line.split(":")
    if len(parts) != 3:
        return
    _, block, state_str = parts
    block     = block.strip().upper()
    state_str = state_str.strip().upper()
    if state_str == "OK":
        return
    if block not in BLOCKS or state_str not in ("OCC","CLR"):
        return

    occupied = (state_str == "OCC")
    with state_lock:
        BLOCKS[block] = occupied

    ls = BLOCK_TO_LINE.get(block)
    if ls:
        ls.update(block, occupied)
        if ls.alert():
            occ = ls.occupied_blocks()
            msg = f"LINE {ls.line_id}: {' & '.join(occ)} OCCUPIED"
            log.warning(f"ALERT -- {msg}")
            push_alert(msg)

# ================================================================
# TRACK GEOMETRY
# ================================================================
TRACK_A_Y = 220
TRACK_B_Y = 152
TRACK_C_Y = 82
MERGE_X   = 328
BLK_W     = 50
BLK_H     = 21

BLOCK_LAYOUT = [
    ("B1",   70,  TRACK_A_Y),
    ("B2",  168,  TRACK_A_Y),
    ("B3",  288,  TRACK_A_Y),
    ("B4",  405,  TRACK_A_Y),
    ("B5",   70,  TRACK_B_Y),
    ("B6",  168,  TRACK_B_Y),
    ("B7",  272,  TRACK_B_Y),
    ("B8",   70,  TRACK_C_Y),
    ("B9",  168,  TRACK_C_Y),
    ("B10", 272,  TRACK_C_Y),
    ("B11", 410,  TRACK_C_Y),
]

# ================================================================
# DRAW
# ================================================================
def draw_track(surf):
    lw = 5
    pygame.draw.line(surf, C_TRACK, (15, TRACK_A_Y), (462, TRACK_A_Y), lw)
    pygame.draw.line(surf, C_TRACK, (15, TRACK_C_Y), (MERGE_X, TRACK_C_Y), lw)
    pygame.draw.line(surf, C_TRACK, (15, TRACK_B_Y), (MERGE_X, TRACK_B_Y), lw)
    steps = 40
    for i in range(steps):
        t0 = i/steps; t1 = (i+1)/steps
        x0 = int(MERGE_X + t0*(462-MERGE_X))
        y0 = int(TRACK_B_Y+(TRACK_C_Y-TRACK_B_Y)*(3*t0**2-2*t0**3))
        x1 = int(MERGE_X + t1*(462-MERGE_X))
        y1 = int(TRACK_B_Y+(TRACK_C_Y-TRACK_B_Y)*(3*t1**2-2*t1**3))
        pygame.draw.line(surf, C_TRACK, (x0,y0), (x1,y1), lw)
    for y in (TRACK_A_Y, TRACK_B_Y, TRACK_C_Y):
        pygame.draw.line(surf, C_TRACK, (15,y-8), (15,y+8), 3)
    pygame.draw.line(surf, C_TRACK, (462,TRACK_A_Y-8),(462,TRACK_A_Y+8),3)
    pygame.draw.line(surf, C_TRACK, (462,TRACK_C_Y-8),(462,TRACK_C_Y+8),3)

def draw_merge_label(surf, font):
    lbl = font.render("MERGE", True, C_YELLOW)
    surf.blit(lbl, (MERGE_X+22, TRACK_B_Y+8))
    rx,ry,rw,rh = MERGE_X-2, TRACK_C_Y-12, 126, TRACK_B_Y-TRACK_C_Y+24
    for x in range(rx, rx+rw, 9):
        pygame.draw.line(surf, C_YELLOW,(x,ry),(min(x+5,rx+rw),ry),1)
        pygame.draw.line(surf, C_YELLOW,(x,ry+rh),(min(x+5,rx+rw),ry+rh),1)
    for y in range(ry, ry+rh, 9):
        pygame.draw.line(surf, C_YELLOW,(rx,y),(rx,min(y+5,ry+rh)),1)
        pygame.draw.line(surf, C_YELLOW,(rx+rw,y),(rx+rw,min(y+5,ry+rh)),1)

def draw_blocks(surf, font, pulse_a):
    with state_lock:
        snap = dict(BLOCKS)
    for (bid,cx,cy) in BLOCK_LAYOUT:
        occ = snap[bid]
        bx,by = cx-BLK_W//2, cy-BLK_H//2
        if occ:
            r = int(C_RED[0]+(C_RED_HI[0]-C_RED[0])*pulse_a)
            g = int(C_RED[1]+(C_RED_HI[1]-C_RED[1])*pulse_a)
            b = int(C_RED[2]+(C_RED_HI[2]-C_RED[2])*pulse_a)
            colour=(r,g,b)
            gs = pygame.Surface((BLK_W+16,BLK_H+16),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*C_RED_HI,int(50*pulse_a+15)),(0,0,BLK_W+16,BLK_H+16),border_radius=8)
            surf.blit(gs,(bx-8,by-8))
        else:
            colour=C_GREEN
        pygame.draw.rect(surf,colour,pygame.Rect(bx,by,BLK_W,BLK_H),border_radius=4)
        num=bid[1:]
        lbl=f"BLK {num}" if len(num)==1 else f"BLK{num}"
        t=font.render(lbl,True,C_WHITE)
        surf.blit(t,t.get_rect(center=(cx,cy)))

def draw_header(surf, fhdr, fsm):
    pygame.draw.rect(surf, C_SURFACE, (0,0,SCREEN_W,28))
    pygame.draw.line(surf, C_BORDER,  (0,28),(SCREEN_W,28),1)
    surf.blit(fhdr.render("RCAS  --  COLLISION AVOIDANCE SYSTEM", True, C_TEXT),(7,7))
    for i,nid in enumerate(["1","2"]):
        col = C_GREEN_HI if nano_online[nid] else C_MUTED
        pygame.draw.circle(surf,col,(SCREEN_W-48+i*22,14),4)
        surf.blit(fsm.render(f"N{nid}",True,col),(SCREEN_W-42+i*22,7))

def draw_line_labels(surf, font):
    for lbl,y in [("A",TRACK_A_Y),("B",TRACK_B_Y),("C",TRACK_C_Y)]:
        surf.blit(font.render(lbl,True,C_MUTED),(4,y-5))

def any_alert():
    return LINE_A.alert() or LINE_B.alert() or LINE_C.alert()

def draw_bottom(surf, fa, fl, ft, pulse_a):
    """Alert banner + hash table debug panel at bottom."""
    BY = 248
    BH = SCREEN_H - BY
    pygame.draw.rect(surf, C_SURFACE,(0,BY,SCREEN_W,BH))
    pygame.draw.line(surf, C_BORDER, (0,BY),(SCREEN_W,BY),1)

    if any_alert():
        # Flashing left panel
        flash = int(180*pulse_a+40)
        pygame.draw.rect(surf,(flash,8,8),(0,BY,196,BH))
        pygame.draw.rect(surf,C_RED_HI,  (0,BY,196,BH),1)
        surf.blit(fa.render("!! COLLISION RISK !!",True,C_WHITE),(5,BY+2))
        lines_alert=[]
        for ls in (LINE_A,LINE_B,LINE_C):
            if ls.alert():
                lines_alert.append(f"Line {ls.line_id}: {'+'.join(ls.occupied_blocks())}")
        surf.blit(fl.render("  "+"  ".join(lines_alert),True,C_RED_HI),(4,BY+15))
        with alert_lock:
            recent=list(alert_log[:3])
        for i,entry in enumerate(recent):
            col=(220-i*30,70,70)
            surf.blit(fl.render(entry,True,col),(4,BY+27+i*13))
    else:
        surf.blit(fa.render("STATUS: ALL LINES CLEAR",True,C_GREEN_HI),(6,BY+10))

    # Hash table state panel (right side)
    hx=200
    surf.blit(ft.render("HASH TABLE [OCCUPIED CHAIN]",True,C_MUTED),(hx,BY+2))
    for row,(lid,ls) in enumerate(zip(["A","B","C"],[LINE_A,LINE_B,LINE_C])):
        chain=ls.occupied_blocks()
        col=C_RED_HI if len(chain)>=2 else (C_GREEN_HI if chain else C_MUTED)
        h_idx=ls.table._hash("OCCUPIED")
        txt=f" Line {lid} bucket[{h_idx}]: [{', '.join(chain) if chain else '--'}]"
        surf.blit(ft.render(txt,True,col),(hx,BY+14+row*13))

# ================================================================
# MAIN
# ================================================================
def main():
    threading.Thread(target=serial_reader,args=(PORT_NANO1,"1"),daemon=True,name="nano1").start()
    threading.Thread(target=serial_reader,args=(PORT_NANO2,"2"),daemon=True,name="nano2").start()

    pygame.init()
    pygame.mouse.set_visible(False)
    flags  = pygame.FULLSCREEN|pygame.NOFRAME if FULLSCREEN else 0
    screen = pygame.display.set_mode((SCREEN_W,SCREEN_H),flags)
    pygame.display.set_caption("RCAS")
    clock  = pygame.time.Clock()

    fhdr = pygame.font.SysFont("monospace",10,bold=True)
    fsm  = pygame.font.SysFont("monospace", 9,bold=True)
    fblk = pygame.font.SysFont("monospace", 9,bold=True)
    fa   = pygame.font.SysFont("monospace",10,bold=True)
    fl   = pygame.font.SysFont("monospace", 8)
    ft   = pygame.font.SysFont("monospace", 8)

    pulse_t=0.0
    log.info("RCAS running. ESC/Q to quit.")

    while True:
        dt=clock.tick(FPS)/1000.0
        pulse_t+=dt
        pulse_a=(1+math.sin(pulse_t*5))/2

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.quit();sys.exit()
            if event.type==pygame.KEYDOWN:
                if event.key in(pygame.K_ESCAPE,pygame.K_q):
                    pygame.quit();sys.exit()

        screen.fill(C_BG)
        for gx in range(0,SCREEN_W,18):
            for gy in range(30,248,18):
                pygame.draw.circle(screen,C_BORDER,(gx,gy),1)

        draw_track(screen)
        draw_merge_label(screen,ft)
        draw_line_labels(screen,fsm)
        draw_blocks(screen,fblk,pulse_a)
        draw_header(screen,fhdr,fsm)
        draw_bottom(screen,fa,fl,ft,pulse_a)

        pygame.display.flip()

if __name__=="__main__":
    main()