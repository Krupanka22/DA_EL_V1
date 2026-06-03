// ================================================================
// nano2.ino  —  Railway Block Sensing  |  NANO 2
// Sensors : S5 (Block 5), S6 (Block 6), S7 (Block 7)   — Line B (Middle)
//           S8 (Block 8), S9 (Block 9), S10(Block10),
//           S11(Block 11)                                — Line C (Top)
// Serial  : 9600 baud  →  Raspberry Pi via USB (/dev/ttyUSB1)
//
// WIRING  (all IR sensor modules share 5V & GND rails):
//   S5  OUT  →  D2
//   S6  OUT  →  D3
//   S7  OUT  →  D4
//   S8  OUT  →  D5
//   S9  OUT  →  D6
//   S10 OUT  →  D7
//   S11 OUT  →  D8
//   All VCC  →  5V pin on Nano
//   All GND  →  GND pin on Nano
//
// IR module OUTPUT is LOW  when object detected (active-LOW)
//
// MESSAGE FORMAT  (one line per state change):
//   2:B5:OCC    →  Nano2, Block5, Occupied
//   2:B5:CLR    →  Nano2, Block5, Clear
// ================================================================

const int NUM_SENSORS = 7;

const int  PINS[NUM_SENSORS]        = { 2, 3, 4, 5, 6, 7, 8 };
const char* BLOCK_IDS[NUM_SENSORS]  = { "B5","B6","B7","B8","B9","B10","B11" };

const unsigned long DEBOUNCE_MS = 60;

bool     confirmed[NUM_SENSORS]     = { false,false,false,false,false,false,false };
bool     rawLast[NUM_SENSORS]       = { false,false,false,false,false,false,false };
unsigned long changeAt[NUM_SENSORS] = { 0,0,0,0,0,0,0 };

// ----------------------------------------------------------------
void setup() {
  Serial.begin(9600);
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(PINS[i], INPUT);
  }
  delay(500);
  Serial.println("2:READY");
}

// ----------------------------------------------------------------
void loop() {
  unsigned long now = millis();

  for (int i = 0; i < NUM_SENSORS; i++) {
    bool raw = (digitalRead(PINS[i]) == LOW);

    if (raw != rawLast[i]) {
      rawLast[i]  = raw;
      changeAt[i] = now;
    }

    if ((now - changeAt[i]) >= DEBOUNCE_MS && raw != confirmed[i]) {
      confirmed[i] = raw;
      sendMsg(i, raw);
    }
  }

  delay(5);
}

// ----------------------------------------------------------------
void sendMsg(int idx, bool occupied) {
  Serial.print("2:");
  Serial.print(BLOCK_IDS[idx]);
  Serial.print(":");
  Serial.println(occupied ? "OCC" : "CLR");
}
