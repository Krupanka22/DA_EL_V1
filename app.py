#!/usr/bin/env python3
"""
app.py  —  Railway Block Monitor  |  Raspberry Pi
=======================================================
- Reads serial data from Nano1 (/dev/ttyUSB0) and
  Nano2 (/dev/ttyUSB1) in background threads
- Maintains live block states (OCC / CLR)
- Serves the animated web dashboard via Flask
- Pushes real-time updates to browser via SocketIO

Run:
    pip install flask flask-socketio pyserial eventlet
    python3 app.py

Then open browser on RPi (or any device on same network):
    http://<raspberry-pi-ip>:5000
    or  http://localhost:5000  on the RPi itself
=======================================================
"""

import threading
import logging
import time
import serial
import serial.tools.list_ports
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ── Flask / SocketIO ──────────────────────────────────────────────
app    = Flask(__name__)
app.config["SECRET_KEY"] = "rly-mon-2024"
sio    = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ── Block state (True = Occupied / RED, False = Clear / GREEN) ────
# B1..B4  from Nano1,  B5..B11 from Nano2
BLOCKS = {f"B{i}": False for i in range(1, 12)}

# Which nano owns which blocks
NANO_BLOCKS = {
    "1": ["B1","B2","B3","B4"],
    "2": ["B5","B6","B7","B8","B9","B10","B11"],
}

# Serial ports — Nano1 on USB0, Nano2 on USB1
SERIAL_PORTS = {
    "1": "/dev/ttyUSB0",
    "2": "/dev/ttyUSB1",
}
BAUD = 9600

# Lock for thread-safe block state writes
state_lock = threading.Lock()

# ── Route ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── SocketIO events ───────────────────────────────────────────────
@sio.on("connect")
def on_connect():
    log.info("Browser connected")
    emit("state", _snapshot())

@sio.on("request_state")
def on_request():
    emit("state", _snapshot())

def _snapshot():
    with state_lock:
        return dict(BLOCKS)

def _broadcast():
    sio.emit("state", _snapshot())

# ── Serial reader ─────────────────────────────────────────────────
def serial_reader(nano_id: str, port: str):
    """
    Connects to one Arduino Nano and reads lines forever.
    Reconnects automatically if the port drops.
    Message format:  <nano_id>:<block_id>:<OCC|CLR>
    Example:         1:B3:OCC
    """
    while True:
        try:
            log.info(f"Nano{nano_id}: connecting on {port}")
            ser = serial.Serial(port, BAUD, timeout=2)
            time.sleep(2)          # let Arduino reset
            ser.reset_input_buffer()
            log.info(f"Nano{nano_id}: connected")

            while True:
                if ser.in_waiting:
                    raw = ser.readline().decode("utf-8", errors="ignore").strip()
                    if raw:
                        _process(raw, nano_id)
                else:
                    time.sleep(0.005)

        except serial.SerialException as e:
            log.error(f"Nano{nano_id} serial error: {e}  — retrying in 5s")
            time.sleep(5)
        except Exception as e:
            log.error(f"Nano{nano_id} unexpected error: {e}")
            time.sleep(5)

def _process(raw: str, nano_id: str):
    """Parse one serial line and update block state."""
    # ignore READY handshake
    if raw.endswith(":READY"):
        log.info(f"Nano{nano_id} is online (READY)")
        return

    parts = raw.split(":")
    if len(parts) != 3:
        log.debug(f"Nano{nano_id} bad message: {raw!r}")
        return

    _, block, state = parts
    block = block.strip().upper()
    state = state.strip().upper()

    if block not in BLOCKS:
        log.debug(f"Unknown block: {block}")
        return
    if state not in ("OCC", "CLR"):
        log.debug(f"Unknown state: {state}")
        return

    occupied = (state == "OCC")

    with state_lock:
        changed = BLOCKS[block] != occupied
        BLOCKS[block] = occupied

    if changed:
        log.info(f"Block {block} → {'OCCUPIED' if occupied else 'CLEAR'}")
        _broadcast()

# ── Main ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start one reader thread per Nano
    for nano_id, port in SERIAL_PORTS.items():
        t = threading.Thread(
            target=serial_reader,
            args=(nano_id, port),
            daemon=True,
            name=f"nano{nano_id}-reader"
        )
        t.start()

    log.info("Starting Flask server on http://0.0.0.0:5000")
    sio.run(app, host="0.0.0.0", port=5000, debug=False)
