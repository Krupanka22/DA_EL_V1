
Claude finished the response
Help me scope an engineering project: phases, dependencies, and risks.

Jun 3
Q: What kind of project is this?
A: New product / feature build

Q: How much do you already have?
A: Just an idea / requirements

Q: What's your team size?
A: [No preference]

Jun 3
Tell me a bit more about the project itself so I can make the scope actually useful — what are you building? A sentence or two on the idea/requirements you have is enough to get started.


1780496172345_Prompt.docx
docx

Jun 3

Viewed a file, ran a command
Viewed a file, ran a command
Great — this is a well-defined embedded systems + web project. Here's the full engineering scope:

🚂 Railway Sensing & Collision Monitoring System — Project Scope
Phases & Dependencies
Phase 1 — Hardware Setup & Arduino Firmware (Foundation — everything depends on this)

Wire IR sensors to each Arduino Nano per pin config table
Write and flash lineA.ino, lineB.ino, lineC.ino with debouncing + serial output at 115200 baud
Validate serial messages manually via Serial Monitor before connecting to Pi
Deliverables: 3 .ino files, wiring diagram, pin config table Duration estimate: 2–4 days

Phase 2 — Raspberry Pi Serial Backend (Depends on Phase 1)

Auto-detect USB serial ports for all 3 Arduinos
serial_manager.py: multi-threaded readers, parse A:S1:ACTIVE messages
train_logic.py: sensor state machine, sequential activation → train position inference, merge conflict detection (S7 + S10 simultaneously active)
app.py: Flask + Flask-SocketIO server, broadcasts state via WebSocket
Deliverables: app.py, serial_manager.py, train_logic.py, requirements.txt Duration estimate: 3–5 days

Phase 3 — Frontend Dashboard (Can be partially done in parallel with Phase 2)

SVG track layout: Line A (S1–S4), Line B (S5–S7), Line C (S8–S11), merge section
Sensor glow animations on activation, animated train movement along tracks
Merge conflict → shared section turns red + collision warning overlay
Logs panel with timestamps + MCU source
Control buttons: Reset, Clear Logs, Demo Mode
Deliverables: index.html, style.css, script.js Duration estimate: 3–5 days

Phase 4 — Integration & Demo Mode (Depends on Phases 2 & 3)

Connect live WebSocket events to frontend animations
Implement Demo Mode: scripted virtual train sequences including a merge conflict scenario
End-to-end test: physical sensor → Pi → browser animation
Duration estimate: 2–3 days

Phase 5 — Hardening & Docs (Final)

Serial reconnection on disconnect, error logging, graceful thread shutdown
Full setup guide: Pi dependencies, run commands, debugging steps
Inline code comments, scalability notes for additional tracks
Duration estimate: 1–2 days

Key Dependencies
Phase	Blocked by
Arduino firmware	Hardware wiring complete
Pi backend	Firmware producing valid serial output
Frontend (live)	Backend WebSocket server running
Integration	Both backend + frontend complete
Demo Mode	Frontend animations working
Risks
High priority:

Serial port instability — USB device enumeration on Pi can assign different /dev/ttyUSBx ports on reboot. Mitigate with udev rules or port auto-detection by querying Arduino identity on startup.
Merge conflict false positives — Two sensors activating within milliseconds (vibration, noise) could trigger spurious conflicts. Mitigate with a time-window debounce in train_logic.py (e.g., both must be active for >200ms).
Sensor debounce on Arduino — IR sensors bounce. Missing this causes duplicate serial messages and corrupted train state.
Medium priority:

Multi-threaded serial reading — Race conditions on shared state between 3 reader threads and the WebSocket broadcaster. Use thread-safe queues (queue.Queue) rather than shared dicts.
Browser animation lag — If WebSocket events arrive faster than the animation frame rate, the UI can pile up. Implement an event queue with frame-rate throttling in script.js.
Low priority:

Pi USB bandwidth — 3 Arduinos at 115200 baud is well within limits, but use a powered USB hub if you see serial errors under load.
Scalability — The architecture (one MCU per line, message format LINE:SENSOR:STATE) already supports adding Line D easily; just requires a new Arduino + frontend SVG extension.
Recommended Build Order
Flash + validate one Arduino first (Line A), get serial messages flowing to Pi terminal
Build serial_manager.py + train_logic.py against that one line before adding the other two
Build the SVG layout statically before wiring up live data — much easier to debug visually
Demo Mode is your best integration test — build it before relying on physical hardware end-to-end
Want me to start generating the actual code for any specific phase — Arduino firmware, the Pi backend, or the frontend dashboard?

Give codes file wise

Jun 3
I'll generate all the files systematically. Let me start with the Arduino firmware, then the Pi backend, then the frontend.


Check frontend design skill
Check frontend design skill
Now let me generate all files one by one.


Created 7 files
Created 7 files
Now the frontend — the most complex file:


Index.html - full railway dashboard frontend
Index.html - full railway dashboard frontend
1780514945057_image.png
Now there are changes
First,
See the image:
and then
There are only Two Arduino Nano used for sensing.

The first Arduino Nano [Nano 1] is used for sensing presence of object on track from sensors [ S1, S2, S3, S4] and second Nano [ Nano 2] is used for sensing from sensors [S5, S6, S7, S8, S9, S10, S11]

Note the structure of the railway track as in image.

All sensors are IR Sensor modules, Each's Vcc has been shorted to 5V Source and GND has been shorted to Ground.

Now, Each Nano would be connected to Raspberry pi through USB Cable

So raspberry pi would have connections through USB0 - to Nano 1
USB1 - to Nano 2

Now i checked and IR Sensor modules are working perfectly
My raspberry pi is connected to a 3.5 TFT Display through GPIO Pins

I want each arduino nano to know which sensor is having any object [Note: Multiple sensors may have objects] 

Here object is basically a train or coach in track, This is a precursor that i am doing for Railway collision avoidance algorithm
as of now, 
Let each nano sense and send to rapsbery pi

In raspberry pi, I want animated Layout of the same map,
Like the image

Instead of S1 - S2 - S3 and all 
put Block 1 - Block 2 - or others

Note the track format

______
___/
_____

and please place the blocks

for each block- i want it to be either green[If sensor detects no objects] or RED [If sensor detects object]

Give the rpi, python code, Arduino nano codes 1&2 including every basic instructions

Show more
1:08 AM
Let me study the image carefully and then generate all the code.


Read frontend design skill
Read frontend design skill
Now let me generate all files cleanly based on the updated design.


Created 4 files, ran a command
Created 4 files, ran a command
Now the dashboard — the most important file:


Created 2 files, read a file
Created 2 files, read a file
Here's everything you need — 6 files total:

What each file does:

File	Purpose
nano1.ino	Senses S1–S4 (Block 1–4), sends 1:B1:OCC / 1:B1:CLR over USB
nano2.ino	Senses S5–S11 (Block 5–11), sends 2:B5:OCC etc. over USB
app.py	Reads both serial ports in threads, serves Flask, pushes WebSocket updates
index.html	Animated 480×320 dashboard — blocks go GREEN (clear) or RED pulsing (occupied), track layout matches your image exactly with the B→C merge curve
requirements.txt	pip install -r requirements.txt on the RPi
SETUP_GUIDE.txt	Full wiring table, USB port assignment, upload steps, autostart config
Key things to note:

Track layout matches your image: Line A (straight bottom), Line B (middle, curves up and merges into Line C after Block 7/10), Line C (top). The merge zone is marked with a dashed yellow box.
Blocks are labelled BLK 1 through BLK 11 instead of S1–S11.
Sized for your 3.5" TFT — 480×320px exactly, no scrollbars.
If your Nanos swap USB ports on reboot, the SETUP_GUIDE shows how to fix that with a udev rule.

Index
Code · HTML 

Nano1
INO 

Nano2
INO 

App
PY 

Requirements
TXT 

Setup guide
TXT 
avin@raspberrypi:~ $ pip3 install flask-socketio pyserial eventleterror: externally-managed-environment× This environment is externally managed╰─> To install Python packages system-wide, try apt install    python3-xyz, where xyz is the package you are trying to    install.       If you wish to install a non-Debian-packaged Python package,    create a virtual environment using python3 -m venv path/to/venv.    Then use path/to/venv/bin/python and path/to/venv/bin/pip. Make    sure you have python3-full installed.       For more information visit http://rptl.io/venvnote: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.hint: See PEP 668 for the detailed specification

2:07 AM
Run this instead:

bash
pip3 install flask flask-socketio pyserial eventlet --break-system-packages
The --break-system-packages flag is safe here — it just bypasses the Debian protection. Your system Python packages won't actually be affected since Flask/pyserial aren't system-critical packages.

If you'd prefer the "clean" way with a virtual environment:

bash
python3 -m venv ~/railway-env
source ~/railway-env/bin/activate
pip install flask flask-socketio pyserial eventlet
python3 app.py
With the venv approach, every time you open a new terminal you'll need to run source ~/railway-env/bin/activate first before python3 app.py. You can avoid that by putting the full path in the systemd service:

ExecStart=/home/pi/railway-env/bin/python3 /home/pi/railway/app.py
The --break-system-packages flag is simpler for a dedicated RPi project like this — go with that.

all it does is update in terminal
It does not even show any UI
coming to the S1-S4 No updated, although arduino connected initially

2:14 AM
Two separate problems. Let me fix both.

Problem 1: No UI — Flask can't find templates/index.html because the folder structure is wrong, or you're running from the wrong directory.

Problem 2: No sensor updates — The serial message format mismatch. The Arduino sends 1:B1:OCC but the parser splits on : and expects exactly 3 parts — the issue is the Arduino println adds \r\n and sometimes garbage on first connect confuses the parser. Also need to verify the port is actually /dev/ttyUSB0.

Let me fix everything into clean, robust files:


Created 4 files, ran a command, read a file
Created 4 files, ran a command, read a file
Here's what was fixed and exactly how to set it up:

What was broken and what changed:

UI not showing — Flask couldn't find index.html because the templates/ folder wasn't in the same directory as app.py. The new app.py uses os.path.dirname(os.path.abspath(__file__)) to always find the templates folder relative to itself, and prints an error + exits immediately if it's missing.

No sensor updates — The message format changed. Arduino now sends N1:B1:OCC (with N1 prefix) so the parser correctly splits into 3 parts: [N1, B1, OCC]. Before, 1:B1:OCC was splitting into ["1","B1","OCC"] but the block lookup was checking "1" as the nano ID rather than reading B1 — the indexing was off.

Exact folder structure needed on the RPi:

~/railway/
    app.py
    templates/
        index.html
Commands to run:

bash
mkdir -p ~/railway/templates
# copy app.py into ~/railway/
# copy index.html into ~/railway/templates/
cd ~/railway
python3 app.py
Then open Chromium: http://localhost:5000

Also run this first if you haven't already (serial port permissions):

bash
sudo usermod -a -G dialout $USER
# then reboot, or run:
sudo chmod 666 /dev/ttyUSB0 /dev/ttyUSB1
To confirm your ports are right before running:

bash
ls /dev/ttyUSB*
# Should show ttyUSB0 and ttyUSB1
# If only one shows, the other Nano isn't recognized yet

App
PY 

Index
Code · HTML 

Nano1
INO 

Nano2
INO 
dont do html
just python file
since in html the browser searchbar and all is filling the entire screen
Just do one python file
of the same

3:32 PM

Check skills available
Check skills available
Pure Python GUI using pygame — one file, fullscreen, no browser needed.


Created a file, read a file
Created a file, read a file
One file, no browser. Here's how to run it:

Install:

bash
pip3 install pygame pyserial --break-system-packages
Run:

bash
python3 railway_monitor.py
What it does:

Opens fullscreen 480×320 directly on the TFT — no browser, no taskbar
Same track layout as your image: Line A (bottom straight), Line B (middle, curves up and merges into C), Line C (top)
Blocks are GREEN when clear, RED pulsing when occupied
Bottom bar shows OCC count, CLR count, live clock
Top bar shows NANO-1 / NANO-2 connection status (lights up green when Arduino connects)
Press ESC or Q to quit
To test without Arduinos (just to verify the display works), temporarily add this near the top of the file after the BLOCKS dict:

python
BLOCKS["B1"] = True
BLOCKS["B5"] = True
You'll see those blocks go red immediately.

To disable fullscreen for desktop testing, change FULLSCREEN = True to FULLSCREEN = False.


Railway monitor
PY 
Thank you, its working properly

Now this project is being done for Experiential learning Component of Design and Analysis of Algorithms course,
and it is about RCAS-RAILWAY COLLISION AVOIDANCE SYSTEM

Now, In a line, If any two sensors are RED [Block - occupied], Then it should display an alert.

That would be my algorithm
[Let it be complicated :)]

How i thought of it initially was,
Let me store OCCUPIED/NOT OCCUPIED as elements (key) of hash table in the Line MCU [Line ARDUINO NANO] and then SENSOR IDs as Values
for Not occupied as key, If multiple sensor IDs are values. Its fine
When storing values, if one sensor is telling occupied, It would undergo with has collision of any other sensors if already occupied.
on case of when lookup of OCCUPIED is searched in the hash table - IF two sensors - alert

Show more
4:19 PM
That's a great idea for a DAA project — using hash collision as the detection mechanism itself is elegant and directly ties the data structure concept to the physical problem.

Let me think through this properly before coding:

Your Algorithm — Refined:

Hash table has fixed size = number of blocks per line
Key = "OCCUPIED" or "CLEAR" → hashed to a bucket index
When a sensor reports OCCUPIED, it inserts (hash("OCCUPIED"), sensor_id) into the table
If that bucket already has an entry → hash collision = two sensors occupied on same line = ALERT
On lookup: if bucket at hash("OCCUPIED") has chain length ≥ 2 → ALERT
This means the collision detection in hardware maps directly to collision chaining in the hash table. That's the core insight for your ELC report.


Created a file, ran a command, read a file
Created a file, ran a command, read a file
Here's exactly how the algorithm works in this code, which you can explain in your ELC:

The Hash Table Algorithm:

Hash Function:  h("OCCUPIED") = sum of ASCII values % table_size
                             = always the same bucket index

Line A table size = 4  (4 blocks)
h("OCCUPIED") = (79+67+67+85+80+73+69+68) % 4  =  constant bucket
When Block 1 gets occupied → insert("OCCUPIED", "B1") → goes into bucket[k]

When Block 3 also gets occupied → insert("OCCUPIED", "B3") → same bucket[k] → HASH COLLISION

The collision itself is the alert. Chain length ≥ 2 means ≥ 2 trains on the same line.

What you see on screen:

Track map (top 75%) — blocks GREEN/RED as before
Bottom panel — splits into:
Left: flashing red !! COLLISION RISK !! with the specific blocks involved, when alert is active. Green ALL LINES CLEAR otherwise.
Right: live hash table state showing Line A bucket[k]: [B1, B3] so you can literally see the chain growing — perfect for your presentation demo

Railway monitor
PY 

............................................


Claude is AI and can make mistakes. Please double-check responses.
Railway monitor · PY
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
 

