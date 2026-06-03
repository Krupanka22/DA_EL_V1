#!/usr/bin/env python3
"""
app.py  —  Railway Block Monitor
Run from the folder that also contains  templates/index.html

    python3 app.py

Then open:  http://localhost:5000
"""

import os, sys, threading, time, logging
import serial, serial.tools.list_ports
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# ── logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ── Flask — look for templates/ NEXT TO this script ───────────────
BASE = os.path.dirname(os.path.abspath(__file__))
app  = Flask(__name__, template_folder=os.path.join(BASE, "templates"))
app.config["SECRET_KEY"] = "railway-2024"
sio  = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Block state  (True = OCCUPIED/RED,  False = CLEAR/GREEN) ──────
BLOCKS = {f"B{i}": False for i in range(1, 12)}
state_lock = threading.Lock()

# ── Serial port config ─────────────────────────────────────────────
# Change these if your ports are different
PORT_NANO1 = "/dev/ttyUSB0"
PORT_NANO2 = "/dev/ttyUSB1"
BAUD       = 9600

# ── Routes ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── SocketIO ──────────────────────────────────────────────────────
@sio.on("connect")
def on_connect():
    log.info("Browser connected")
    emit("state", _snap())

@sio.on("request_state")
def on_req():
    emit("state", _snap())

def _snap():
    with state_lock:
        return dict(BLOCKS)

def _push():
    sio.emit("state", _snap())

# ── Serial reader ─────────────────────────────────────────────────
def reader(port, nano_label):
    """
    Reads one serial port forever, reconnects on error.
    Expected message format:   N1:B3:OCC\r\n
    """
    while True:
        try:
            log.info(f"{nano_label}: opening {port}")
            with serial.Serial(port, BAUD, timeout=2) as ser:
                time.sleep(2)                  # let Arduino boot/reset
                ser.reset_input_buffer()
                log.info(f"{nano_label}: port open — waiting for data")

                while True:
                    raw = ser.readline()       # bytes, ends with \n
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        log.info(f"{nano_label} RX: {line!r}")
                        parse(line, nano_label)

        except serial.SerialException as e:
            log.error(f"{nano_label}: serial error — {e}  (retry in 5s)")
            time.sleep(5)
        except Exception as e:
            log.error(f"{nano_label}: unexpected error — {e}")
            time.sleep(5)

def parse(line, src):
    """
    Accept:  N1:B3:OCC  /  N1:B3:CLR  /  N2:B10:OCC  etc.
    Also ignores READY messages.
    """
    parts = line.split(":")
    if len(parts) != 3:
        return

    _, block, state = parts
    block = block.strip().upper()
    state = state.strip().upper()

    if state == "OK":          # READY:OK — just a handshake
        log.info(f"{src} is online")
        _push()                # refresh browser pills
        return

    if block not in BLOCKS:
        log.warning(f"Unknown block: {block!r}")
        return
    if state not in ("OCC", "CLR"):
        log.warning(f"Unknown state: {state!r}")
        return

    occupied = (state == "OCC")
    with state_lock:
        changed = BLOCKS[block] != occupied
        BLOCKS[block] = occupied

    if changed:
        log.info(f"Block {block} → {'OCCUPIED' if occupied else 'CLEAR'}")
        _push()

# ── Check templates folder exists ─────────────────────────────────
tpl = os.path.join(BASE, "templates", "index.html")
if not os.path.exists(tpl):
    log.error(f"MISSING FILE: {tpl}")
    log.error("Make sure templates/index.html is in the same folder as app.py")
    sys.exit(1)

# ── Start serial threads ──────────────────────────────────────────
threading.Thread(target=reader, args=(PORT_NANO1, "NANO1"), daemon=True).start()
threading.Thread(target=reader, args=(PORT_NANO2, "NANO2"), daemon=True).start()

# ── Run ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("="*50)
    log.info("Railway Block Monitor starting")
    log.info(f"Templates folder : {BASE}/templates/")
    log.info(f"Nano1 port       : {PORT_NANO1}")
    log.info(f"Nano2 port       : {PORT_NANO2}")
    log.info("Open browser at  : http://localhost:5000")
    log.info("="*50)
    sio.run(app, host="0.0.0.0", port=5000, debug=False)