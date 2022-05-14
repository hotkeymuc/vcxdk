/*

Low-level tests
This is used to probe the compiler and the hardware.
It was used to develop/reverse-engineer the low-level screen and keyboard routines.

*/

#include <stdiomin.h>

//#include <vcxdk.h>
//#include <memory.h>
//#include <screen.h>
//#include <keyboard.h>
//#include <ui.h>


//#define mem(x) *(unsigned char *)(x)
//#define bin(a,b,c,d,e,f,g,h) (a*128 + b*64 + c*32 + d*16 + e*8 + f*4 + g*2 + h)


//__far const char STR_HELLO[] = "Hello, world!";
__far const char STR_TITLE[] = "test.c!";


/*
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
	
	78CB: current SCAN CODE (FF if none, 0x00 - 0x5e, without 7,f)
	
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
void test_ui(void) {
	// Call ui.h
	//alert("Hello.");
	//alert(&STR_TITLE);
	alert((__far char *)&STR_TITLE);
}
*/

/*
void test_pointer(void) {
	// Test CARTRIDGE_ROM_POINTER()
	__far char *test = CARTRIDGE_ROM_POINTER(&STR_TITLE);
	c = *(char *)test;
	screen_draw_glyph(0, 0, c);
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





/*
void test_ascii(void) {
	// Draw ASCII table
	x = 0;
	y = 0;
	for(i = 0; i < 256; i++) {
		c = (i & 0xff);
		screen_draw_glyph(x, y, (word)c);
		
		x += 8;
		if (x >= SCREEN_WIDTH) {
			x = 0;
			y += 8;
			if (y >= SCREEN_HEIGHT) {
				y = 0;
			}
		}
	}
}
*/


/*
void test_ports(void) {
	int i, j, f;
	word x, y;
	char c;
	byte v;
	word p, p2;
	
	// Port monitor
	screen_clear();
	
	p = 0x7800;
	while(1) {
		
		// Draw current port
		x = 0;
		y = 0;
		draw_hex16(0, 0, p);
		
		if (confirm("Monitor those addresses?") == 1) {
			// Monitor for a few frames
			
			// Draw labels
			p2 = p;
			x = 0;
			for(i = 0; i < 4; i++) {
				
				y = 8;
				for(j = 0; j < 16; j++) {
					//screen_draw_hex16(x, y, p2);
					//screen_draw_glyph(x+4*8, y, (word)'=');
					screen_draw_hex8(x, y, p2 & 0xff);
					screen_draw_glyph(x+(2*8), y, (word)'=');
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
						//screen_draw_hex16(x, y, p2);
						//screen_draw_glyph(x+4*8, y, (word)'=');
						//screen_draw_hex8(x, y, p2 & 0xff);
						//screen_draw_glyph(x+(2*8), y, (word)'=');
						
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
*/



/*
void test_keyboard(void) {
	word x, y;
	char c;
	int i;
	
	// Test keyboard
	screen_clear();
	
	x = 0;
	y = 0;
	screen_draw_glyph(x, y, 'E'); x += 8;
	screen_draw_glyph(x, y, 'n'); x += 8;
	screen_draw_glyph(x, y, 't'); x += 8;
	screen_draw_glyph(x, y, 'e'); x += 8;
	screen_draw_glyph(x, y, 'r'); x += 8;
	screen_draw_glyph(x, y, ' '); x += 8;
	screen_draw_glyph(x, y, 's'); x += 8;
	screen_draw_glyph(x, y, 'o'); x += 8;
	screen_draw_glyph(x, y, 'm'); x += 8;
	screen_draw_glyph(x, y, 'e'); x += 8;
	screen_draw_glyph(x, y, 't'); x += 8;
	screen_draw_glyph(x, y, 'h'); x += 8;
	screen_draw_glyph(x, y, 'i'); x += 8;
	screen_draw_glyph(x, y, 'n'); x += 8;
	screen_draw_glyph(x, y, 'g'); x += 8;
	screen_draw_glyph(x, y, ':'); x += 8;
	screen_draw_glyph(x, y, ' '); x += 8;
	
	i = 0;
	do {
		screen_draw_glyph(x, y, '_');	// Cursor
		
		c = getchar();
		i++;
		
		if (c == KEY_BACKSPACE) {
			screen_draw_glyph(x, y, ' ');
			x -= 8;
			continue;
		}
		
		screen_draw_glyph(x, y, (byte)c);
		
		x += 8;
		if (x >= SCREEN_WIDTH) {
			x = 0;
			y += 8;
		}
	} while ((i < 30) && (c != KEY_ENTER));
	
}
*/


void test_gets(void) {
	int c;
	char s[32];
	char *ps;
	byte l;
	
	ps = &s[0];
	l = 0;
	c = 0;
	while(c != 10) {
		
		screen_draw_glyph(screen_x, screen_y, '_');
		c = getchar();
		screen_draw_glyph(screen_x, screen_y, ' ');
		
		if ((c != 0xff) && (c != 0x00)) {
			
			if (c == 8) {
				if (l > 0) {
					putchar(8);
					ps--;
					l--;
				}
			} else {
				putchar(c);
				*ps++ = c;
				l++;
			}
		}
	}
	*ps++ = 0;
	puts(s);
}



//volatile int bar = 0x7fff;
//static int foo = 0x1234;
//char baz[16];

void main(void) {

	
	screen_clear();
	
	puts(CARTRIDGE_ROM_POINTER("Hello."));
	puts(CARTRIDGE_ROM_POINTER("This is a test."));
	//printf(CARTRIDGE_ROM_POINTER("Test\r\n"));
	//printf(CARTRIDGE_ROM_POINTER("Test %d, %d\n"), 1, 2);
	//puts(&baz);
	
	while(1) {
		test_gets();
	}
}
