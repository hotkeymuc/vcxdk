#ifndef __SCREEN_H
#define __SCREEN_H

/*
Simple LCD frame buffer access for the VTech Genius Leader 8008 CX

2022-05-10 Bernhard "HotKey" Slawik
*/


#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 144
#define SCREEN_BYTES_PER_ROW 60	// 240 pixels, 2bpp = 60 bytes per row
#define SCREEN_WORDS_PER_ROW 30	// 240 pixels, 2bpp = 30 words per row
#define VRAM_START 0x3300	// Start of video memory: 0x3300
#define SCREEN_BUFFER 0x3340	// Start of frame buffer (2bpp): 0x3340


void screen_clear(void) {
	int i;
	unsigned short *p;
	
	p = (unsigned short *)SCREEN_BUFFER;
	for(i = 0; i < (SCREEN_HEIGHT*SCREEN_WORDS_PER_ROW); i++) {
		*p++ = 0x0000;
	}
}

#include "font_console_8x8.h"

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


#endif
