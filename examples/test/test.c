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

0300 = continue
0340 = continue
0380 = continue
03C0 = continue

0400 = high static values
0440 = high static values
0480 = high static values
04c0 = high static values

0500 = high static values
0540 = high static values
0580 = high static values
05c0 = high static values

0600 = high static values
0640 = high static values
0680 = high static values
06c0 = high static values

0700 = high static values
0740 = high static values
0780 = high static values
07c0 = high static values

0800 = zeros and static values
0840 = zeros and static values
0880 = zeros and static values / freeze!
08c0 = zeros and static values

0900 = zeros and static values / hard crash!
0940 = 13 00 00 00
0980 = 13 00 00 00
09c0 = 13 00 00 00

0a00 = 13 00 00 00
0a40 = 13 00 00 00
0a80 = 13 00 00 00
0ac0 = 13 00 00 00

0b00 = 13 00 00 00
0b40 = 13 00 00 00
0bc0 = (crashed!)
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
FD40 (jittery): like FC40
FD80 (jittery): 00, but reacts to touch
FDC0 (jittery): like FC40

FE00 = static values
FE40 = static values and FF 00
FE80 = ones and zeros, shortly flashing
FEC0 = static values

FF00 = HARD CRASH!
FF40 = happy values and FF 00.
FF80 = flashing 01 00
FFC0 = flashing 01 00

*/
//#include <stdio.h>

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned long int dword;

#define mem(x) *(unsigned char *)(x)
#define bin(a,b,c,d,e,f,g,h) (a*128 + b*64 + c*32 + d*16 + e*8 + f*4 + g*2 + h)


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



// Those must be aligned properly (assembler takes care of this and adds trailing zero bytes)
//__far const char STR_HELLO[] = "Hello, world!";
__far const char STR_TITLE[] = "test.c!";

#include "font_console_8x8.h"


// Some trials agains VTech Genius Leader 8008 CX [de] firmware traps
void alert(__far char *text) {
	(void)text;	// Disable "unused" warning
	
	__asm__("push    $2, era");
	
	// Show alert
	__asm__("movd    $0x034191, (r1,r0)");	// Dunno what this param does
	__asm__("adduw   $-0x8, sp");
	__asm__("storw   r0, 0x4(sp)");
	__asm__("storw   r1, 0x6(sp)");
	
	//__asm__("movd    .str_htk, (r1,r0)");
	// Copy function parameter (r3,r2) to (r1, r0)
	__asm__("movw    r3, r1");
	__asm__("movw    r2, r0");
	__asm__("adduw   $0x10, r1");	// Add the cartridge ROM base address (0x100000)
	
	__asm__("storw   r0, 0(sp)");
	__asm__("storw   r1, 0x2(sp)");
	
	__asm__("movb    $0, r4");	// Dunno what this param does
	__asm__("movd    $0x084D40, (r3,r2)");	// Dunno what this param does
	__asm__("bal     (ra,era), 0x198CC4");	// show_info_popup_r1r0 (0x018CC4 + internal ROM offset 0x180000)
	
	__asm__("adduw   $0x8, sp");
	
	// Clean up
	__asm__("pop     $2, era");
	
}



#pragma set_options("-Wno-return-type")	// Suppress warning "control reaches end of non-void function", because we manually set R0
int prompt_from_rom(__far char *title, __far char *text) {
	(void)title;
	(void)text;
	
	__asm__("push    $2, era");
	
	// Show prompt
	__asm__("movd    $0x034191, (r1,r0)");	// Dunno what this param does...
	__asm__("push    $2, r0");
	
	// Title parameter is in (r3,r2)
	//__asm__("movd    .str_hello, (r3,r2)");	// Set pointer of title
	__asm__("adduw   $0x10, r3");	// ...add the cartridge ROM base address (0x100000)
	
	// Text parameter is in (r5,r4)
	//__asm__("movd    .str_htk, (r5,r4)");	// Set pointer of text
	__asm__("adduw   $0x10, r5");	// ...add the cartridge ROM base address (0x100000)
	//XXX: __asm__("adduw   $0x10, r5");	// XXX ...add the RAM base address (not 00, 01, 02, 03, 04, 07, 08, 0f, 10, 18, 20)
	
	__asm__("bal     (ra,era), 0x1805C4");	// prompt_yesno__title_r3r2__text_r5r4__sys5c4 (0x0005C4 + internal ROM offset 0x180000)
	__asm__("adduw   $0x4, sp");
	
	// Check the result in r0
	//__asm__("cmpb    $0x1, r0");	// 1 = YES, 0 = NO
	//__asm__("beq     .start");	// Back to start
	
	// Clean up
	__asm__("pop     $2, era");
	
	// NOTE!
	// "return X" statement intentionally omitted, because register R0 is already set and should remain as-is.
	// So: ignore the warning "control reaches end of non-void function" (-Wno-return-type)
	
}
#pragma reset_options()


//const char HEXTABLE[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};


#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 144
#define SCREEN_BYTES_PER_ROW 60	// 240 pixels, 2bpp = 60 bytes per row
#define SCREEN_WORDS_PER_ROW 30	// 240 pixels, 2bpp = 30 words per row
#define VRAM_START 0x3300	// Start of video memory: 0x3300
#define SCREEN_BUFFER 0x3340	// Start of frame buffer (2bpp): 0x3340

void draw_glyph(word x, word y, word g) {
	__far byte *dp;
	byte iy;
	//unsigned char *p;
	word *p;
	byte d;
	
	// Source pointer to glyph in ROM
	dp = (byte *)&font_console_8x8[g % 256][0];
	__asm__("adduw   $0x10, r0");	// ...add the cartridge ROM base address (0x100000)
	__asm__("storw   r0,8(sp)");
	
	// Destination pointer to screen buffer
	//p = (byte *)SCREEN_BUFFER;
	//p += (y * SCREEN_BYTES_PER_ROW);	// 240 pixels at 2 bits-per-pixel = 60 bytes per row
	//p += (x >> 2);	// 2 bits per pixel = 1/4 byte per column
	
	p = (word *)SCREEN_BUFFER;
	p += (y * SCREEN_WORDS_PER_ROW);	// 240 pixels at 2 bits-per-pixel = 60 bytes per row
	p += (x >> 3);	// 2 bits per pixel = 1/8 word per column
	
	for(iy = 0; iy < 8; iy++) {
		d = *dp++;
		/*
		// Set as two bytes at a time
		// Left 4 pixels fit into first byte
		*p++ = 3 *	// Color (0=off/white, 1=bright, 2=medium, 3=black)
		(
			  (d & 0x80) >> 1
			| (d & 0x40) >> 2
			| (d & 0x20) >> 3
			| (d & 0x10) >> 4
		);
		// Right 4 pixels fit into second byte
		*p++ = 3 *	// Color (0=off/white, 1=bright, 2=medium, 3=black)
		(
			  (d & 0x08) << 3
			| (d & 0x04) << 2
			| (d & 0x02) << 1
			| (d & 0x01)
		);
		
		p += (SCREEN_BYTES_PER_ROW - 2);	// 60 bytes per row, we already set 2 bytes (8 pixels at 2bpp)
		*/
		
		// Set as one word at a time
		*p = 3 *	// Color (0=off/white, 1=bright, 2=medium, 3=black)
		(
			  (d & 0x80) >> 1
			| (d & 0x40) >> 2
			| (d & 0x20) >> 3
			| (d & 0x10) >> 4
			
			| (d & 0x08) << 11
			| (d & 0x04) << 10
			| (d & 0x02) << 9
			| (d & 0x01) << 8
		);
		p += SCREEN_WORDS_PER_ROW;
	}
}

void draw_hexdigit(word x, word y, byte v) {
	if (v <= 0x09)
		draw_glyph(x  , y, (word)('0'+v));
	else if (v <= 0x0f)
		draw_glyph(x  , y, (word)('A'+v-0x0a));
	else
		draw_glyph(x  , y, (word)'?');
}
void draw_hex8(word x, word y, byte v) {
	//draw_glyph(x  , y, HEXTABLE[v >> 4]);
	//draw_glyph(x+8, y, HEXTABLE[v & 0xf]);
	draw_hexdigit(x  , y, (v >> 4));
	draw_hexdigit(x+8, y, (v & 0x0f));
}
void draw_hex16(word x, word y, word v) {
	draw_hexdigit(x   , y, (v >> 12)      );
	draw_hexdigit(x+ 8, y, (v >>  8) & 0xf);
	draw_hexdigit(x+16, y, (v >>  4) & 0xf);
	draw_hexdigit(x+24, y, (v      ) & 0xf);
}

void main(void) {
	int i, j, f;
	word x, y;
	char c;
	byte v;
	word p, p2;
	
	//alert("Hello.");
	//alert(&STR_HELLO);
	//alert((__far char *)&STR_HELLO);
	
	
	/*
	// Manually draw letter "A"
	mem(SCREEN_BUFFER + 60*0 + 0) = bin(0,0, 0,0, 1,1, 1,1);	mem(SCREEN_BUFFER + 60*0 + 1) = bin(1,1, 0,0, 0,0, 0,0);
	mem(SCREEN_BUFFER + 60*1 + 0) = bin(0,0, 1,1, 1,1, 0,0);	mem(SCREEN_BUFFER + 60*1 + 1) = bin(1,1, 1,1, 0,0, 0,0);
	mem(SCREEN_BUFFER + 60*2 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*2 + 1) = bin(0,0, 1,1, 1,1, 0,0);
	mem(SCREEN_BUFFER + 60*3 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*3 + 1) = bin(0,0, 1,1, 1,1, 0,0);
	mem(SCREEN_BUFFER + 60*4 + 0) = bin(1,1, 1,1, 1,1, 1,1);	mem(SCREEN_BUFFER + 60*4 + 1) = bin(1,1, 1,1, 1,1, 0,0);
	mem(SCREEN_BUFFER + 60*5 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*5 + 1) = bin(0,0, 1,1, 1,1, 0,0);
	mem(SCREEN_BUFFER + 60*6 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*6 + 1) = bin(0,0, 1,1, 1,1, 0,0);
	mem(SCREEN_BUFFER + 60*7 + 0) = bin(0,0, 0,0, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*7 + 1) = bin(0,0, 0,0, 0,0, 0,0);
	*/
	/*
	// Draw a few iconic symbols
	draw_glyph(16 +  0, 0, 219);	// all black
	draw_glyph(16 +  8, 0, 177);	// pattern 01010101
	draw_glyph(16 + 16, 0, 219);	// all black
	draw_glyph(16 + 24, 0, 16);	// Triangle to right
	draw_glyph(16 + 32, 0, 219);	// all black
	draw_glyph(16 + 40, 0, 219);	// all black
	draw_glyph(16 + 48, 0, 92);	// Backslash
	draw_glyph(16 + 56, 0, 219);	// all black
	draw_glyph(16 + 64, 0, 179);	// VLine 2 bit wide
	draw_glyph(16 + 72, 0, 219);	// all black
	*/
	
	x = 0;
	y = 0;
	for(i = 0; i < 256; i++) {
		c = (i & 0xff);
		draw_glyph(x, y, (word)c);
		
		x += 8;
		if (x >= SCREEN_WIDTH) {
			x = 0;
			y += 8;
			if (y >= SCREEN_HEIGHT) {
				y = 0;
			}
		}
	}
	
	/*
	while(1) {
		
		if (prompt_from_rom((__far char *)&STR_TITLE, (__far char *)"More?") == 1) {
			x = 0;
			y = 8;
			for(i = 0; i < 256; i++) {
				c = (i & 0xff);
				draw_glyph(x, y, c);
				
				x += 8;
				if (x >= SCREEN_WIDTH) {
					x = 0;
					y += 8;
					if (y >= SCREEN_HEIGHT) {
						y = 0;
					}
				}
			}
		} else {
			break;
		}
	}
	*/
	
	//alert("Monitor");
	
	for(i = 0; i < (SCREEN_HEIGHT*SCREEN_BYTES_PER_ROW); i++) {
		mem(SCREEN_BUFFER + i) = 0x00;
	}
	
	p = 0xf800;
	
	while(1) {
		
		// Draw current port
		x = 0;
		y = 0;
		draw_hex16(0, 0, p);
		
		if (prompt_from_rom((__far char *)&STR_TITLE, (__far char *)"Monitor those addresses?") == 1) {
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
				
				draw_hex8(64, 0, f);	// Frame counter
				
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
