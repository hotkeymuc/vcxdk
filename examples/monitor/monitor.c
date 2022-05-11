/*
Rudimentary port monitor

Allows to view the current state of up to 64 ports at once.
Was used to find the keyboard buffer and touchpad state.

2022-05-10 Bernhard "HotKey" Slawik
*/

//#include <stdio.h>

#include <vcxdk.h>

#include <memory.h>
#include <screen.h>
#include <keyboard.h>
#include <ui.h>

//#define mem(x) *(unsigned char *)(x)
#define bin(a,b,c,d,e,f,g,h) (a*128 + b*64 + c*32 + d*16 + e*8 + f*4 + g*2 + h)

__far const char STR_TITLE[] = "monitor.c";


/*
0000 = 00
0040 = zeros and values
0080 = 00
00C0 = static values

0100 = static values
0140 = 16 static values, then FF
0180 = some FF, then static values
01C0 = static values and 00

0200 = 00
0240 = some low-value 16bit table
0280 = continue
02C0 = continue

03.. = continue
04.. = high static values
05.. = high static values
06.. = high static values
07.. = high static values
08.. = zeros and static values

0900 = zeros and static values / hard crash!
0940 = 13 00 00 00
0980 = 13 00 00 00
09c0 = 13 00 00 00
0a.. = 13 00 00 00
0b.. = 13 00 00 00

...

40.. = FF FC 3F F0 00 00 3F F0 4F F0 00 00 FF F0 ... 00 00 00 ..

...

6... = 00

70.. = 00
71.. = 00
72.. = 00
73.. = 00
7400 = 48x FF, c0, 00, 01, c0, 00 ...
7440 = 37x 00, 55, 54, c5, 55....
7480 = 6F, FE, 55, 55, 55, 55, ... 5E, D5, 55, 55, 55, 55, ...
74C0 = FF, FF, FF, 55, 55, 78, B5, ED, 55, 55, 40, 00, 05, 55, 56, FF... AA, AA, AA, AA, A8, ....
75.. = static values, around 55 and FF
76.. = static values, around 55, AA and 00 and FF
77.. = 00
77C0 = 00 and static values


7800 = NICE VALUES! Touch Pad coordinates!
	7810: accessed in timer INT at 038D80
	7812: accessed in timer INT at 038D80
	
	Counter: Incremented by INT at ROM 038D24
		7814 = counter (LOWL, fast change)
		7815 = counter (LOWH, ~2 changes per second)
		7816 = counter (HIGHL, slow change)
		7817 = counter (HIGHH)
	
	7818: compared against 0x00
	781A: compared against 0x16
	
	TouchPad:
		7820/7822 = X-coordinate (low on the right, high on the left)
		7821/7823 = Y-coordinate
		7818/7824 = 00/01 if touch down

7840 = 00s and a single one (7847)
7880 = 00s and a single one (789C)

78C0 = Keyboard state!
	78C3-78C9: keyboard buffer (4 x 16 bit), stores scancodes
	78CF: current IN index in buffer; used by ROM (sys3c8)	037B2C:	1F D8 CF 78	D81F 78CF	storb   r0, 0x078CF
	78D0: current OUT index in buffer; used by ROM (sys3c8)	037B28:	1F D8 D0 78	D81F 78D0	storb   r0, 0x078D0
	
	78CB: current SCAN CODE (FF if none)
		
		5E = SoftKey: "E-Mail"
		...
		0E = POWER ON
		0D = POWER OFF
		0C = "5"
		0B = "T"
		0A = "F"
		09 = "V"
		08 = SPACE
		
		06 = SoftKey 6 "Computerpraxis"
		05 = SoftKey 3 "Quiz-Fragen"
		04 = "4"
		03 = "R"
		02 = "D"
		01 = "C"
		00 = CONTROL LEFT
		
		FF=none
		
	78F4 used by ROM: 037EAA:	1F D8 F4 78	D81F 78F4	storb   r0, 0x078F4
	78D1 used by ROM: 037EAE:	1F D8 D1 78	D81F 78D1	storb   r0, 0x078D1
	

	7960: used by ROM (sys5a0)
	7962: used by ROM (sys5a0)

7980 = 00
7A.. = 00 and a few statics
7B.. = 00 and a few statics
7C.. = 00 and a few statics

7D00
	7D14: used by ROM 
	7D15: used by ROM (sys5a0)
	7D16: Mouse button pressed; used by ROM (sys5a0)
	7D18: used by ROM (sys5a0)
	7D19: used by ROM

7D40 = 00 and static vars
7D80 = 00 and static vars
7DC0 = 00 and static vars
	7DF4 is checked after pressing POWER OFF button. Can prevent a power off if set to 0x00! used by ROM: 037C28:	32 80      	8032     	loadb   0(r9), r1	; r9 == 0x7DF4

7E.. = 00 and static vars

7F.. = 00

8000 = 00

...


F800 = 1F CA (flashing)
F840 = 1F CA (flashing)
F880 = 1F CA (flashing)
F8c0 = 1F CA (flashing)

F900 = xx CA and 1F CA (flashing)
F940 = xx CA and 1F CA (flashing)
F980 = 1F CA (flashing)
F9c0 = 1F CA (flashing)

FA00 = 16 values, then 1F CA (flashing)
FA40 = crashes after 0x3F frames
FA80 = 1F CA (flashing)
FAC0 = 1F CA (flashing)

FB00 = 1F CA (flashing)
FB40 = 1F CA (flashing)
FB80 = 1F CA (flashing)
FBc0 = 1F CA (flashing)

FC00 (jittery):	Reacts to touch pad!
	E4/FF on idle
	becomes EF on left button held
	becomes F7 on right button held
	becomes D3/D7/F8 when touching touch pad
FC40 (jittery): counts slowly up while fingers are on touchpad?!
FCC0 (jittery): reacts to touch

FD00 (jittery): like FC00
	FD20 used by ROM: 038CAC:	1F 98 20 FD	981F FD20	loadb   0x0FD20, r0	; and 0xF8
	FD22 used by ROM: 038CB6:	1F 98 22 FD	981F FD22	loadb   0x0FD22, r0	; and 0xFA
	FD24 used by ROM: ~038CB6 and timer INT
	FD26 used by ROM: ~038CB6 and timer INT
	FD28 used by ROM: ~038CB6
	
FD40 (jittery): like FC40
FD80 (jittery): 00, but reacts to touch
FDC0 (jittery): like FC40
	FDC4 UART? used by ROM: 037DC0:	1F 98 C4 FD	981F FDC4	loadb   0x0FDC4, r0

FE00 = static values
FE40 = static values and FF 00
FE80 = ones and zeros, shortly flashing
FEC0 = static values
	FEE2 UART? used by ROM: 037DD4:	1F 98 E2 FE	981F FEE2	loadb   0x0FEE2, r0

FF00 = HARD CRASH!
	FF04 used by ROM: 037DFE:	1F 98 04 FF	981F FF04	loadb   0x0FF04, r0

FF40 = happy values and FF 00.
	FF60-FF70 used by ROM: 038C84:	D2 04 68 FF	04D2 FF68	storb   $0x9, 0x0FF68
FF80 = flashing 01 00
FFC0 = flashing 01 00

*/


//register int *foovar __asm__("r9");
/*
unsigned char *reserve_stack(unsigned int size) {
	(void)size;	// Suppress warning of unused param
	
	// Parameter is in register R2
	__asm__("subw r2, sp");	// Reserve r2 bytes on stack
	__asm__("movw sp, r0");	// Remember address
	__asm__("subw $-2, r0");	// Correct for auto-generated function epilogue (sp+2)
	
	// NOTE!
	// "return X" statement intentionally omitted, because register r0 is already set and should remain as-is
	// So ignore the warning "control reaches end of non-void function".
}
*/

/*
int probe_mem(unsigned int addr) {
	// Probe memory: 0=ROM, 1=RAM, -1=unknown
	
	unsigned char v;
	unsigned char v_old;
	unsigned char v_new;
	
	// Read old
	v_old = *(unsigned char *)addr;
	
	// Set to new value
	v_new = (v_old ^ 0xff);
	*(unsigned char *)addr = v_new;
	
	// Read back
	v = *(unsigned char *)addr;
	
	// Compare
	if (v == v_old) {
		// Read only
		return 0;
	}
	
	if (v == v_new) {
		// Writable!
		
		// Reset
		*(unsigned char *)i = v_old;
		
		return 1;
	}
	
	// Neither old nor new value!
	return -1;
}
*/






void main(void) {
	int i, j, f;
	word x, y;
	byte v;
	word p, p2;
	
	
	//alert("Monitor");
	
	/*
	for(i = 0; i < (SCREEN_HEIGHT*SCREEN_BYTES_PER_ROW); i++) {
		mem(SCREEN_BUFFER + i) = 0x00;
	}
	*/
	screen_clear();
	
	
	// Binary search for start address (as long as we do not have working keyboard input)
	p = 0x7800;
	/*
	if (prompt("Start 0x8000-0xFFFF") == 1) {
		// 0x8000 - 0xFFFF
		if (prompt("Start 0xC000-0xFFFF") == 1) {
			// 0xC000 - 0xFFFF
			if (prompt("Start 0xE000-0xFFFF") == 1) {
				p = 0xe000;
			} else {
				p = 0xc000;
			}
		} else {
			// 0x8000 - 0xBFFF
			if (prompt("Start 0xA000-0xBFFF") == 1) {
				p = 0xa000;
			} else {
				p = 0x8000;
			}
		}
	} else {
		// 0x0000 - 0x7FFF
		if (prompt("Start 0x4000-0x7FFF") == 1) {
			// 0x4000 - 0x7FFF
			if (prompt("Start 0x6000-0x7FFF") == 1) {
				// 0x6000 - 0x7FFF
				//p = 0x6000;
				if (prompt("Start 0x7000-0x7FFF") == 1) {
					//p = 0x7000;
					if (prompt("Start 0x7800-0x7FFF") == 1) {
						p = 0x7800;	// 7800 = the most interesing bits!
					} else {
						p = 0x7000;
					}
				} else {
					p = 0x6000;
				}
			} else {
				// 0x4000 - 0x5FFF
				if (prompt("Start 0x5000-0x5FFF") == 1) {
					p = 0x5000;
				} else {
					p = 0x4000;
				}
			}
		} else {
			// 0x0000 - 0x3FFF
			if (prompt("Start 0x2000-0x3FFF") == 1) {
				p = 0x2000;
			} else {
				p = 0x0000;
			}
		}
	}
	*/
	
	
	
	
	while(1) {
		
		// Draw current port
		x = 0;
		y = 0;
		draw_hex16(0, 0, p);
		
		if (prompt("Monitor those addresses?") == 1) {
			// Monitor for a few frames
			
			// Draw labels
			p2 = p;
			x = 0;
			for(i = 0; i < 4; i++) {
				
				y = 8;
				for(j = 0; j < 16; j++) {
					//draw_hex16(x, y, p2);
					//draw_glyph(x+4*8, y, (word)'=');
					draw_hex8(x, y, p2 & 0xff);
					draw_glyph(x+(2*8), y, (word)'=');
					p2++;
					y += 8;
				}
				
				x += (8 * 6);
			}
			
			// Go for a few rounds
			for (f = 0; f < 128; f++) {
				
				draw_hex8(64, 0, (byte)f);	// Frame counter
				
				p2 = p;
				
				x = 0 + (8 * 3);	// Start to the right of first row of labels
				for(i = 0; i < 4; i++) {
					
					y = 8;
					for(j = 0; j < 16; j++) {
						//draw_hex16(x, y, p2);
						//draw_glyph(x+4*8, y, (word)'=');
						//draw_hex8(x, y, p2 & 0xff);
						//draw_glyph(x+(2*8), y, (word)'=');
						
						v = mem(p2++);
						draw_hex8(x, y, v);
						
						y += 8;
					}
					
					x += (8 * 6);
				}
				
			}
		
		} else {
			p += 0x40;
		}
	}
	
}
