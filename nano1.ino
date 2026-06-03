// ================================================================
// nano1.ino  —  Railway Block Sensing  |  NANO 1
// Sensors : S1 (Block 1), S2 (Block 2), S3 (Block 3), S4 (Block 4)
// Track   : Bottom straight line  (Line A)
// Serial  : 9600 baud  →  Raspberry Pi via USB (/dev/ttyUSB0)
//
// WIRING  (all IR sensor modules share 5V & GND rails):
//   S1 OUT  →  D2
//   S2 OUT  →  D3
//   S3 OUT  →  D4
//   S4 OUT  →  D5
//   All VCC →  5V pin on Nano
//   All GND →  GND pin on Nano
//
// IR module OUTPUT is LOW  when object detected (active-LOW)
//
// MESSAGE FORMAT  (one line per state change):
//   1:B1:OCC    →  Nano1, Block1, OBject present (Occupied)
//   1:B1:CLR    →  Nano1, Block1, Clear
// ================================================================

const int NUM_SENSORS = 4;

// Digital pins for S1..S4
const int  PINS[NUM_SENSORS]         = { 2, 3, 4, 5 };
const char* BLOCK_IDS[NUM_SENSORS]   = { "B1", "B2", "B3", "B4" };

// Debounce
const unsigned long DEBOUNCE_MS = 60;

bool     confirmed[NUM_SENSORS]   = { false, false, false, false };
bool     rawLast[NUM_SENSORS]     = { false, false, false, false };
unsigned long changeAt[NUM_SENSORS] = { 0, 0, 0, 0 };

// ----------------------------------------------------------------
void setup() {
  Serial.begin(9600);
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(PINS[i], INPUT);
  }
  delay(500);
  Serial.println("1:READY");   // handshake so RPi knows Nano1 is alive
}

// ----------------------------------------------------------------
void loop() {
  unsigned long now = millis();

  for (int i = 0; i < NUM_SENSORS; i++) {
    bool raw = (digitalRead(PINS[i]) == LOW);   // LOW = object present

    // detect raw edge
    if (raw != rawLast[i]) {
      rawLast[i]  = raw;
      changeAt[i] = now;
    }

    // accept only after stable for DEBOUNCE_MS
    if ((now - changeAt[i]) >= DEBOUNCE_MS && raw != confirmed[i]) {
      confirmed[i] = raw;
      sendMsg(i, raw);
    }
  }

  delay(5);
}

// ----------------------------------------------------------------
void sendMsg(int idx, bool occupied) {
  Serial.print("1:");
  Serial.print(BLOCK_IDS[idx]);
  Serial.print(":");
  Serial.println(occupied ? "OCC" : "CLR");
}
