/*
VTech CX BusIO / Logic Analyzer
===============================

Description:
Arduino DUE sketch to "sniff" the system bus of a VTech CX series computer.

History:
A completely new try.
After having "finished" the whole Z80 based VTech Genius series, I now want to investigate the CR16B based "CX" series.
These are (among others): GL5005X, GL8008CX, BlackMagicCX, GL6600CX?, BS9009CXL?, ePower?, ...

I added some "spinal taps" to my 8008CX so I can read/werite to the bus. I don't have the proper card edge connectors, so I am trying to dump ROMs using the main PCB's cartridge port.
Fingers crossed!

Since the CX series is 3.3V I will use an Arduino Due for a change.

2022-03-03 Bernhard "HotKey" Slawik

-----

Infos:
In order to read the bus quickly, I should try to bundle the address bus and data bus to one Due Port if possible.
See: https://docs.arduino.cc/hacking/hardware/PinMappingSAM3X
DUE port manipulation: https://forum.arduino.cc/t/arduino-due-how-to-direrct-port-access/251656/2

To get the highest data rate, I am using the NATIVE port ("SerialUSB") for the application.
The programming port (Serial) coan not handle the thruput.



Port A:
  X PA0 CANTX
  X PA1 CANRX
    PA2 A7
    PA3 A6
    PA4 A5
  X
    PA6 A4
    PA7 D31
  X
  X
  X PA10  RX1
  X PA11  TX1
  x PA12  RX2
  x PA13  TX2
    PA14  D23
    PA15  D24     nCE
    PA16  A0
  X PA17  SDA1
  X PA18  SCL2
    PA19  D42
    PA20  D43
  X PA21  LED "TX"
    PA22  A3
    PA23  A2
    PA24  A1
  X PA25  (MISO)
  X PA26  (MOSI)
  X PA27  (SCLK)
  X PA28+PC29 D10 (NPCS0)
    PA29+PC26 D4
  X
  X


Port B:
  X PB10  VBOF
  X PB11  ID
  X PB12  SDA
  X PB13  SCL
    PB14  D53
  X PB15  DAC0
  X PB16  DAC1
    PB17  A8
    PB18  A9
    PB19  A10
    PB20  A11
    PB21  D52
  X
  X PB23  (unconnected)
  X
    PB25  D2
    PB26  D22
    PB27  D13 / Amber LED


Port C:
  X ---
    PC1  D33      ADDR0
    PC2  D34      ADDR1
    PC3  D35      ADDR2
    PC4  D36      ADDR3
    PC5  D37      ADDR4
    PC6  D38      ADDR5
    PC7  D39      ADDR6
    PC8  D40      ADDR7
    PC9  D41      ADDR8
  X ---
  X ---
    PC12  D51     ADDR9
    PC13  D50     ADDR10
    PC14  D49     ADDR11
    PC15  D48     ADDR12
    PC16  D47     ADDR13
    PC17  D46     ADDR14
    PC18  D45     ADDR15
 ?? PC19  D44     ADDR16
  X ---
    PC21  D9      ADDR17
    PC22  D8      ADDR18
    PC23  D7      ADDR19
    PC24  D6      CS2     
    PC25  D5      nWE     
    PC26+PA29 D4  --
  X ---
 ?? PC28  D3      --
    PC29+PA28 D10 --
  X PC30  LED "RX"
  X ---


Port D:
    PD0 D25   DATA0
    PD1 D26   DATA1
    PD2 D27   DATA2
    PD3 D28   DATA3
  x PD4 TX3
  x PD5 RX3
    PD6 D29   DATA4
    PD7 D11   DATA5
    PD8 D12   DATA6
    PD9 D30   DATA7
    PD10  D32

*/

#define PIN_nCE 24      //D24 = PA15
//#define set_nCE_HIGH  digitalWrite(PIN_nCE, HIGH)
//#define set_nCE_LOW   digitalWrite(PIN_nCE, LOW)
//#define set_nCE_HIGH    REG_PIOA_PDSR |= (uint32_t)(1L << 15)
//#define set_nCE_LOW     REG_PIOA_PDSR &= ~(uint32_t)(1L << 15)
//#define set_nCE_HIGH    REG_PIOA_ODSR |= (1 << 15)
//#define set_nCE_LOW     REG_PIOA_ODSR &= ~(1 << 15)
#define set_nCE_HIGH    REG_PIOA_SODR = (1 << 15)
#define set_nCE_LOW     REG_PIOA_CODR = (1 << 15)


#define PIN_nOE 23      //D23 = PA14
//#define set_nOE_HIGH  digitalWrite(PIN_nOE, HIGH)
//#define set_nOE_LOW   digitalWrite(PIN_nOE, LOW)
//#define set_nOE_HIGH    REG_PIOA_PDSR |= (uint32_t)(1L << 14)
//#define set_nOE_LOW     REG_PIOA_PDSR &= ~(uint32_t)(1L << 14)
//#define set_nOE_HIGH    REG_PIOA_ODSR |= (1 << 14)
//#define set_nOE_LOW     REG_PIOA_ODSR &= ~(1 << 14)
#define set_nOE_HIGH    REG_PIOA_SODR = (1 << 14)
#define set_nOE_LOW     REG_PIOA_CODR = (1 << 14)


#define PIN_nWR 5       //D5  = PC25
//#define set_nWR_HIGH  digitalWrite(PIN_nWR, HIGH)
//#define set_nWR_LOW   digitalWrite(PIN_nWR, LOW)
//#define set_nWR_HIGH    REG_PIOC_PDSR |= (uint32_t)(1L << 25)
//#define set_nWR_LOW     REG_PIOC_PDSR &= ~(uint32_t)(1L << 25)
//#define set_nWR_HIGH    REG_PIOC_ODSR |= (1 << 25)
//#define set_nWR_LOW     REG_PIOC_ODSR &= ~(1 << 25)
#define set_nWR_HIGH    REG_PIOC_SODR = (1 << 25)
#define set_nWR_LOW     REG_PIOC_CODR = (1 << 25)


#define PIN_nCS2 6      //D6  = PC24
//#define set_nCS2_HIGH digitalWrite(PIN_nCS2, HIGH)
//#define set_nCS2_LOW  digitalWrite(PIN_nCS2, LOW)
//#define set_nCS2_HIGH   REG_PIOC_PDSR |= (uint32_t)(1L << 24)
//#define set_nCS2_LOW    REG_PIOC_PDSR &= ~(uint32_t)(1L << 24)
//#define set_nCS2_HIGH   REG_PIOC_ODSR |= (1 << 24)
//#define set_nCS2_LOW    REG_PIOC_ODSR &= ~(1 << 24)
#define set_nCS2_HIGH    REG_PIOC_SODR = (1 << 24)
#define set_nCS2_LOW     REG_PIOC_CODR = (1 << 24)


#define SERIAL_DEVICE SerialUSB // SerialUSB = Arduino Due "native"
//#define SERIAL_BAUD 115200
#define SERIAL_BAUD 2000000

#define put(s) SERIAL_DEVICE.println(s)
#define put_(s) SERIAL_DEVICE.print(s)

#define NUM_ADDR 20 //17

// Arduino pin numbers of addresses
const uint8_t PIN_ADDR[NUM_ADDR] = {
  33, // A0
  34, // A1
  35, // A2
  36, // A3
  37, // A4
  38, // A5
  39, // A6
  40, // A7
  
  41, // A8
  51, // A9
  50, // A10
  49, // A11
  48, // A12
  47, // A13
  46, // A14
  45, // A15
  
  44, // A16
  9, // A17
  8, // A18
  7, // A19
};
const uint8_t PIN_DATA[8] = {
  /*
  // Data on PortC
  9,  // DATA0
  8,  // DATA1
  7,  // DATA2
  6,  // DATA3
  5,  // DATA4
  4,  // DATA5
  3,  // DATA6
  10, // DATA7
  */
  
  // Data on PortD
  25, // DATA0
  26, // DATA1
  27, // DATA2
  28, // DATA3
  29, // DATA4
  11, // DATA5
  12, // DATA6
  30, // DATA7
};

const char HEX_DIGITS[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};
const char BIN_DIGITS[2] = {'0', '1'};

void printByte(char c) {
  SERIAL_DEVICE.print(c);
}
void printHEX_4(uint8_t d) {
  printByte(HEX_DIGITS[d % 0x10]);
}
void printHEX_8(uint8_t d) {
  printHEX_4(d >> 4);
  printHEX_4(d % 0x10);
}
void printHEX_16(uint16_t d) {
  printHEX_8(d >> 8);
  printHEX_8(d % 0x100);
}
void printHEX_32(uint32_t d) {
  printHEX_16(d >> 16);
  printHEX_16(d % 0x10000);
}


byte readByte() {
  while (SERIAL_DEVICE.available() < 1) {
    delayMicroseconds(100);
  }
  char c = SERIAL_DEVICE.read();
  return c;
}
uint8_t readHEX_4() {
  return parseHEX_4(readByte());
}
uint8_t parseHEX_4(char c) {
  if ((c >= '0') && (c <= '9')) return (c - '0');
  if ((c >= 'A') && (c <= 'F')) return 10 + (c - 'A');
  if ((c >= 'a') && (c <= 'f')) return 10 + (c - 'a');
  return 0xff;
}

uint8_t readHEX_8() {
  char c0 = readByte();
  char c1 = readByte();
  return parseHEX_8(c0, c1);
}
uint8_t parseHEX_8(char c0, char c1) {
  uint8_t r0 = parseHEX_4(c0);
  uint8_t r1 = parseHEX_4(c1);
  return (r0 << 4) | r1;
}

uint16_t readHEX_16() {
  char c0 = readByte();
  char c1 = readByte();
  char c2 = readByte();
  char c3 = readByte();
  return parseHEX_16(c0, c1, c2, c3);
}
uint16_t parseHEX_16(char c0, char c1, char c2, char c3) {
  uint16_t r0 = parseHEX_8(c0, c1);
  uint16_t r1 = parseHEX_8(c2, c3);
  return (r0 << 8) | r1;
}


uint32_t readHEX_32() {
  char c0 = readByte();
  char c1 = readByte();
  char c2 = readByte();
  char c3 = readByte();
  char c4 = readByte();
  char c5 = readByte();
  char c6 = readByte();
  char c7 = readByte();
  return parseHEX_32(c0, c1, c2, c3, c4, c5, c6, c7);
}
uint32_t parseHEX_32(char c0, char c1, char c2, char c3, char c4, char c5, char c6, char c7) {
  //return ((uint32_t)parseHEX_16(c0, c1, c2, c3)) << 16 + (uint32_t)parseHEX_16(c4, c5, c6, c7);
  
  uint32_t r0 = parseHEX_16(c0, c1, c2, c3);
  uint32_t r1 = parseHEX_16(c4, c5, c6, c7);
  uint32_t r = (r0 << 16L) | r1;  // Check if this actually works! Big numbers are hard...
  return r;
}


void pinmode_hi_z() {
  // Set all pins "high impedance" to not disturb a running system
  uint8_t i;
  
  set_nWR_HIGH;
  set_nCE_HIGH;
  set_nCS2_HIGH;
  set_nOE_HIGH;
  
  
  pinMode(PIN_nCE, INPUT);
  pinMode(PIN_nCS2, INPUT);
  pinMode(PIN_nOE, INPUT);
  pinMode(PIN_nWR, INPUT);
  
  for(i = 0; i < 8; i++) {
    pinMode(PIN_DATA[i], INPUT);
  }
  
  for(i = 0; i < NUM_ADDR; i++) {
    //digitalWrite(PIN_ADDR[i], LOW);
    pinMode(PIN_ADDR[i], INPUT);
  }
}

void pinmode_acquire_r() {
  int i;

  set_nWR_HIGH;
  set_nCE_HIGH;
  set_nCS2_HIGH;
  set_nOE_HIGH;
  
  // Set up pins
  pinMode(PIN_nCE, OUTPUT);
  digitalWrite(PIN_nCE, HIGH);
  //set_nCE_HIGH;

  pinMode(PIN_nCS2, OUTPUT);
  digitalWrite(PIN_nCS2, HIGH);
  //set_nCS2_HIGH;
  
  pinMode(PIN_nWR, OUTPUT);
  digitalWrite(PIN_nWR, HIGH);
  //set_nWR_HIGH;
  
  pinMode(PIN_nOE, OUTPUT);
  digitalWrite(PIN_nOE, HIGH);
  //set_nOE_HIGH;
  
  
  // Use Arduino pin numbering here
  // Data pins
  for(i = 0; i < 8; i++) {
    pinMode(PIN_DATA[i], INPUT);
    digitalWrite(PIN_DATA[i], LOW);
  }
  
  // Addr on PortD
  for(i = 0; i < NUM_ADDR; i++) {
    pinMode(PIN_ADDR[i], OUTPUT);
    digitalWrite(PIN_ADDR[i], LOW);
  }
}

void pinmode_acquire_w() {
  int i;

  set_nWR_HIGH;
  set_nCE_HIGH;
  set_nCS2_HIGH;
  set_nOE_HIGH;
  
  // Set up pins
  pinMode(PIN_nCE, OUTPUT);
  digitalWrite(PIN_nCE, HIGH);
  //set_nCE_HIGH;

  pinMode(PIN_nCS2, OUTPUT);
  digitalWrite(PIN_nCS2, HIGH);
  //set_nCS2_HIGH;
  
  pinMode(PIN_nWR, OUTPUT);
  digitalWrite(PIN_nWR, HIGH);
  //set_nWR_HIGH;
  
  pinMode(PIN_nOE, OUTPUT);
  digitalWrite(PIN_nOE, HIGH);
  //set_nOE_HIGH;
  
  
  // Use Arduino pin numbering here
  // Data pins
  for(i = 0; i < 8; i++) {
    pinMode(PIN_DATA[i], OUTPUT);
    //digitalWrite(PIN_DATA[i], LOW);
  }
  
  // Addr on PortD
  for(i = 0; i < NUM_ADDR; i++) {
    pinMode(PIN_ADDR[i], OUTPUT);
    digitalWrite(PIN_ADDR[i], LOW);
  }
}

void set_addr(uint32_t a) {
  /*
  // Naive (slow!)
  uint8_t i;
  for(i = 0; i < NUM_ADDR; i++) {
    digitalWrite(PIN_ADDR[i], (a & (1L << (uint32_t)i)) ? HIGH : LOW);
  }
  */
  
  // Bit shift magic
  //uint32_t p = REG_PIOC_PDSR;
  uint32_t p = REG_PIOC_ODSR;

  //put_("Encoding a=0x"); printHEX_32(a); put_(" onto port=0x"); printHEX_32(p);
  
  p = (uint32_t)( p & (uint32_t)0b11111111000100000000110000000001) // Clear address bits, keep all unused ones as-is
    | (uint32_t)((a & (uint32_t)0b00000000000000000000000111111111) << 1)  // A0-A8 to PC1-PC9
    | (uint32_t)((a & (uint32_t)0b00000000000000011111111000000000) << 3)  // A9-A16 to PC12-PC19
    | (uint32_t)((a & (uint32_t)0b00000000000011100000000000000000) << 4)  // A17-A19 to PC21-PC23
    ;
  //put_(" -- it becomes 0x"); printHEX_32(p); put();
  
  //REG_PIOC_PDSR = p;
  //REG_PIOC_CODR = ...;
  //REG_PIOC_SODR = ...;
  REG_PIOC_ODSR = p;
}

uint32_t get_addr() {
  uint8_t i;
  uint32_t a = 0L;

  /*
  // Naive reading (slow!)
  for(i = 0; i < NUM_ADDR; i++) {
    if (digitalRead(PIN_ADDR[i]) == HIGH)
      a |= 1L << (uint32_t)i;
  }
  */
  
  // Bit shift magic
  uint32_t p = REG_PIOC_PDSR; // Pin Data Status Regiser = current level on pin
  //a = ((p >> 1) & 0x01ff) | (((p >> 12) & 0xff) << 9) | (((p >> 21) & 0x07) << 17);
  a = ((p & 0b000000000000001111111110) >> 1)  // PC1-PC9 to A0-A8
    | ((p & 0b000011111111000000000000) >> 3)  // PC12-PC19 to A9-A16
    | ((p & 0b111000000000000000000000) >> 4)  // PC21-PC23 to A17-A19
  ;
  return a;
}


uint8_t get_data() {
  // Just read data off the bus (without OE)
  uint32_t v;

  // Read the port
  v = REG_PIOD_PDSR;  // Pin Data Status Regiser = current level on pin
  
  // Decode
  uint8_t d;
  d = (v & 0x0fL)          // D0-D3 from PD0-PD3
    | ((v >> 2) & 0xf0);  // D4-D7 from PD6-PD9

  return d;
}

void set_data(uint8_t d) {
  // Latch data to the bus
  uint32_t v;

  // Get old register value
  
  // Read the port
  //v = REG_PIOD_PDSR;
  v = REG_PIOD_ODSR;
  
  // Encode data onto it
  /*
    PD0 D25   DATA0
    PD1 D26   DATA1
    PD2 D27   DATA2
    PD3 D28   DATA3
  x PD4 TX3
  x PD5 RX3
    PD6 D29   DATA4
    PD7 D11   DATA5
    PD8 D12   DATA6
    PD9 D30   DATA7
    PD10  D32
  */

  // For PortD
  v =  (uint32_t)(v & (uint32_t)0b11111111111111111111110000110000)  // & ~0b1111001111  // Mask out the bits we are about to set
    | ((uint32_t)(d & 0x0f))           // Set bits DATA0-DATA3 onto PD0-PD3
    | ((uint32_t)(d & 0xf0) << 2);    // Set bits DATA4-DATA7 onto PD6-PD9

  // Write modified register value back
  //REG_PIOD_SOSR = ...;
  //REG_PIOD_COSR = ...;
  REG_PIOD_ODSR = v;
}

uint8_t read_data(uint32_t addr) {
  // Perform a whole read cycle
  
  uint8_t d;
  
  // Make sure we don't accidentally overwrite stuff
  set_nWR_HIGH;
  
  // Set address to be read
  set_addr(addr);
  
  // Activate chip
  set_nCS2_LOW;
  set_nCE_LOW;
  
  delayMicroseconds(1); //@TODO: Set according to timing in data sheet of ROM/EPROM/EEPROM/SRAM

  // Request to read
  set_nOE_LOW;

  //delayNanoseconds(70);
  delayMicroseconds(1);
  
  // Now read what's on the bus
  
  // Simply read
  d = get_data();

  // Read until settled
  uint8_t d_old;
  do {
    delayMicroseconds(1);
    d_old = d;
    d = get_data();
  } while(d != d_old);

  
  // De-activate chip
  set_nOE_HIGH;
  set_nCE_HIGH;
  set_nCS2_HIGH;
  
  return d;
}


uint8_t write_data(uint32_t addr, uint8_t d) {
  // Perform a whole write cycle
  
  // Make sure we don't accidentally overwrite other stuff
  set_nCE_HIGH;
  set_nWR_HIGH;
  set_nOE_HIGH; // OE state doesn't matter for WRITE sais KM68V1000 manual

  delayMicroseconds(1);
  
  // Set address to be written to
  set_addr(addr);

  delayMicroseconds(1);
  
  // Activate chip
  set_nCE_LOW;
  set_nCS2_LOW;
  
  //delayMicroseconds(1);
  
  // Set data to be written
  set_data(d);

  //delayMicroseconds(1);
  
  // Perform write
  set_nWR_LOW;
  
  // delay of > 70ns required
  delayMicroseconds(1);
  
  // End write cycle: This edge triggers the write
  set_nWR_HIGH;

  // data must stay for a few nanoseconds after WE is high again
  delayMicroseconds(1);
  
  // De-activate chip
  set_nCE_HIGH;
  set_nCS2_HIGH;

  //delayMicroseconds(1);
  
  return d;
}

void dump_rom(uint32_t addr_start, uint32_t len) {
  // Dump the ROM
  int i;
  
  uint32_t a = addr_start;
  uint32_t end_address = addr_start + len;
  
  //put("--------------------");
  while(a < end_address) {
    char s[16];
    
    sprintf(s, "%08X: ", a);
    put_(s);

    for(i = 0; i < 16; i++) {
      // Simple
      //v = read_data(a);

      // Re-read until two consecutive reads yield the same
      uint8_t v, v_old;
      v = read_data(a);
      do {
        v_old = v;
        v = read_data(a);
      } while(v != v_old);
      sprintf(s, "%02X", v);
      put_(s);

      a++;
    }
    put("");
  }
  //put("--------------------");
  
}

bool is_monitoring;
uint32_t current_address;
void setup() {
  uint8_t i;
  
  // In doubt: Leave bus alone on startup!
  pinmode_hi_z();
  
  // Required on Due!
  while (!SERIAL_DEVICE) {};
  SERIAL_DEVICE.begin(SERIAL_BAUD);
  

  put("# VTechGLXBusIO");
  put("# Bernhard \"HotKey\" Slawik");
  put_("# "); put_(__DATE__); put_(" "); put(__TIME__);
  
  // Wait for serial to settle
  delay(500);

  /*
  pinmode_acquire();
  dump_rom(0x000000L, 0x100000L);
  put("--------------------");
  */
  
  // Leave the bus alone
  pinmode_hi_z();
  is_monitoring = false;
  current_address = 0x0000;
}



void loop() {
  char s[16];
  uint32_t addr;
  uint32_t l;
  uint8_t d;
  uint32_t v;
  
  if (is_monitoring) {
    // Read bus without interfering
    addr = get_addr();
    d = get_data();
    
    sprintf(s, "%06X=%02X", addr, d);
    put(s);
    
    //sprintf(s, "%06X%02X\n", addr, d);
    //put_(s);
    
    //delay(10);
  }
  

  while (SERIAL_DEVICE.available()) {
    // get the new byte:
    char c = (char)SERIAL_DEVICE.read();
    switch(c) {
      case 't':
        // Test
        /*
        put_("Enter 16 bit (4 digit) hex:");
        v = readHEX_16();
        put_("I parsed that as: ");
        printHEX_16(v);
        put_(" / ");
        printHEX_32(v);
        put();
        
        put_("Enter 32 bit (8 digit) hex:");
        v = readHEX_32();
        put_("I parsed that as: ");
        printHEX_32(v);
        put();
        */
        pinmode_acquire_r();
        dump_rom(0x00000000, 0x100);
        pinmode_hi_z();
        break;
      
      case '?':
        // Show current status of pins
        addr = get_addr();
        d = get_data();
        put_("# Status: addr=0x"); printHEX_32(addr); put_(", data=0x"); printHEX_8(d);
        //put_(", nCS2="); put_((digitalRead(PIN_nCS2) == HIGH) ? "HIGH" : "LOW");
        put();
        break;
      
      case 'r':
        addr = readHEX_32();
        d = readHEX_8();
        put_("# Reading 0x"); printHEX_32(addr); put_(" = 0x");
        
        //pinmode_acquire_r();
        d = read_data(addr);
        //pinmode_hi_z();
        
        printHEX_8(d); put();
        break;
      
      case 'w':
        addr = readHEX_32();
        d = readHEX_8();
        put_("# Writing 0x"); printHEX_8(d); put_(" to 0x"); printHEX_32(addr); put_(": ");
        
        pinmode_acquire_r();
        put_("before=0x"); printHEX_8(read_data(addr)); put_(", ");

        pinmode_acquire_w();
        write_data(addr, d);

        pinmode_acquire_r();
        put_("after=0x"); printHEX_8(read_data(addr)); put(".");
        
        pinmode_hi_z();
        break;
      
      case 'W':
        // e.g. W0000004000000008f0f1f2f3f4f5f6f7
        // e.g. W0000000000000008f0f1f2f3f4f5f6f7
        // e.g. Change Filename to "HAXX0RED":  W00001b8c000000084841585830524544
        addr = readHEX_32();
        l = readHEX_32();
        
        //pinmode_acquire_w();
        
        while (l > 0) {
          d = readHEX_8();
          write_data(addr, d);
          addr++;
          l--;
        }
        
        //pinmode_hi_z();
        break;
        
      case 'a':
        pinmode_acquire_r();
        break;
      
      case 'A':
        pinmode_acquire_w();
        break;
        
      case 'z':
        // Hi-Z
        pinmode_hi_z();
        break;
        
      case 'd':
        // dump
        // e.g. d0000000000000100
        // e.g. d00001b8000000100
        
        // Ask for address and length
        //addr = 0x000000L;
        //l = 0x100000L;
        addr = readHEX_32();
        l = readHEX_32();
        put_("# Dumping 0x"); printHEX_32(addr); put_(" - 0x"); printHEX_32(addr + l); put("...");
        
        //pinmode_acquire_r();
        dump_rom(addr, l);
        //pinmode_hi_z();
        break;
        
      case 'm':
        // monitor
        //pinmode_hi_z();
        is_monitoring = true;
        break;

      case 'M':
      case 's':
      case 'q':
        //pinmode_hi_z();
        is_monitoring = false;
        break;

    }
  }
}
