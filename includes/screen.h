#ifndef __SCREEN_H
#define __SCREEN_H

/*
Simple LCD frame buffer access for the VTech Genius Leader 8008 CX

2022-05-10 Bernhard "HotKey" Slawik
*/

//#include "memory.h"	// for CARTRIDGE_ROM_POINTER() for font

#define SCREEN_WIDTH 240
#define SCREEN_HEIGHT 144
#define SCREEN_BYTES_PER_ROW 60	// 240 pixels, 2bpp = 60 bytes per row
#define SCREEN_WORDS_PER_ROW 30	// 240 pixels, 2bpp = 30 words per row
#define VRAM_START 0x3300	// Start of video memory: 0x3300
#define SCREEN_BUFFER 0x3340	// Start of frame buffer (2bpp): 0x3340

static volatile word screen_x = 0;
static volatile word screen_y = 0;

void screen_clear(void) {
	int i;
	unsigned short *p;
	
	p = (unsigned short *)SCREEN_BUFFER;
	for(i = 0; i < (SCREEN_HEIGHT*SCREEN_WORDS_PER_ROW); i++) {
		*p++ = 0x0000;
	}
	screen_x = 0;
	screen_y = 0;
}

void screen_scroll(word rows) {
	word i;
	unsigned short *p1;
	unsigned short *p2;
	
	p1 = (unsigned short *)SCREEN_BUFFER;
	p2 = (unsigned short *)SCREEN_BUFFER + (rows * SCREEN_WORDS_PER_ROW);
	
	// Copy up
	for(i = 0; i < ((SCREEN_HEIGHT-rows)*SCREEN_WORDS_PER_ROW); i++) {
		*p1++ = *p2++;
	}
	
	// Clear rest
	for(i = 0; i < (rows*SCREEN_WORDS_PER_ROW); i++) {
		*p1++ = 0x0000;
	}
}

void screen_set_at(word x, word y, byte col) {
	byte b;
	unsigned short *p;
	p = (unsigned short *)SCREEN_BUFFER + (y * SCREEN_WORDS_PER_ROW);
	p += (x >> 3);	// 2bpp = 8 pixels per word
	b = (((x & 0x7) << 2) | 8) & 0xf;	// 16-bit wrap-around: 8, 10, 12, 14, 0, 2, 4, 6
	*p = (
		(*p & (0xffff ^ (0x3 << b)))	// ~(0x3 << b)
		| (col << b)
	);
}

/*
// Manually draw the letter "A"
#define mem(x) *(unsigned char *)(x)
#define bin(a,b,c,d,e,f,g,h) (a*128 + b*64 + c*32 + d*16 + e*8 + f*4 + g*2 + h)

mem(SCREEN_BUFFER + 60*0 + 0) = bin(0,0, 0,0, 1,1, 1,1);	mem(SCREEN_BUFFER + 60*0 + 1) = bin(1,1, 0,0, 0,0, 0,0);
mem(SCREEN_BUFFER + 60*1 + 0) = bin(0,0, 1,1, 1,1, 0,0);	mem(SCREEN_BUFFER + 60*1 + 1) = bin(1,1, 1,1, 0,0, 0,0);
mem(SCREEN_BUFFER + 60*2 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*2 + 1) = bin(0,0, 1,1, 1,1, 0,0);
mem(SCREEN_BUFFER + 60*3 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*3 + 1) = bin(0,0, 1,1, 1,1, 0,0);
mem(SCREEN_BUFFER + 60*4 + 0) = bin(1,1, 1,1, 1,1, 1,1);	mem(SCREEN_BUFFER + 60*4 + 1) = bin(1,1, 1,1, 1,1, 0,0);
mem(SCREEN_BUFFER + 60*5 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*5 + 1) = bin(0,0, 1,1, 1,1, 0,0);
mem(SCREEN_BUFFER + 60*6 + 0) = bin(1,1, 1,1, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*6 + 1) = bin(0,0, 1,1, 1,1, 0,0);
mem(SCREEN_BUFFER + 60*7 + 0) = bin(0,0, 0,0, 0,0, 0,0);	mem(SCREEN_BUFFER + 60*7 + 1) = bin(0,0, 0,0, 0,0, 0,0);
*/


//#define FONT_FULL_8BIT	// Include all 8-bit ascii characters?
#ifdef FONT_FULL_8BIT
	#define FONT_CONSOLE_8X8_FULL_8BIT	// Include all 8-bit ascii characters?
#endif

#include "font_console_8x8.h"

// Copy font info over
#define FONT_DATA FONT_CONSOLE_8X8_DATA
#define FONT_WIDTH FONT_CONSOLE_8X8_WIDTH	// 8
#define FONT_HEIGHT FONT_CONSOLE_8X8_HEIGHT	// 8
#define FONT_FIRST FONT_CONSOLE_8X8_FIRST
#define FONT_LAST FONT_CONSOLE_8X8_LAST
#define FONT_SIZE FONT_CONSOLE_8X8_SIZE
#define FONT_COLOR 3	// Color (0=off/white, 1=bright, 2=medium, 3=black)


// Draw one glyph of the font
void screen_draw_glyph(word x, word y, word g) {
	__far const byte *dp;
	byte iy;
	//unsigned char *p;
	word *p;
	byte d;
	
	if (g < FONT_FIRST) return;
	if (g > FONT_LAST) return;
	g -= FONT_FIRST;
	
	// Source pointer to glyph in ROM
	/*
	// Fix the pointer to point to cartridge ROM
	dp = (byte *)&font_console_8x8[g][0];
	__asm__("adduw   $0x10, r0");	// ...add the cartridge ROM base address (0x100000)
	__asm__("storw   r0,8(sp)");
	*/
	//dp = &FONT_DATA[g][0];	// Font lives as constant in cartridge ROM
	dp = ROM_POINTER((__far void *)&FONT_DATA[g][0]);	// Font lives as constant in cartridge ROM
	
	
	// Destination pointer to screen buffer
	
	// Byte-wide access:
	//p = (byte *)SCREEN_BUFFER;
	//p += (y * SCREEN_BYTES_PER_ROW);	// 240 pixels at 2 bits-per-pixel = 60 bytes per row
	//p += (x >> 2);	// 2 bits per pixel = 1/4 byte per column
	
	// Word-wide access:
	p = (word *)SCREEN_BUFFER;
	p += (y * SCREEN_WORDS_PER_ROW);	// 240 pixels at 2 bits-per-pixel = 30 words per row
	p += (x >> 3);	// 2 bits per pixel = 1/8 word per column
	
	// Draw all rows of font
	for(iy = 0; iy < 8; iy++) {
		d = *dp++;
		
		/*
		// Set as two bytes
		// Left 4 pixels fit into first byte
		*p++ = FONT_COLOR *	// Color (0=off/white, 1=bright, 2=medium, 3=black)
		(
			  (d & 0x80) >> 1
			| (d & 0x40) >> 2
			| (d & 0x20) >> 3
			| (d & 0x10) >> 4
		);
		// Right 4 pixels fit into second byte
		*p++ = FONT_COLOR *	// Color (0=off/white, 1=bright, 2=medium, 3=black)
		(
			  (d & 0x08) << 3
			| (d & 0x04) << 2
			| (d & 0x02) << 1
			| (d & 0x01)
		);
		
		p += (SCREEN_BYTES_PER_ROW - 2);	// 60 bytes per row, we already set 2 bytes (8 pixels at 2bpp)
		*/
		
		// Set 8 pixels at once using one word at a time
		*p = FONT_COLOR *	// Color (0=off/white, 1=bright, 2=medium, 3=black)
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
		p += SCREEN_WORDS_PER_ROW;	// Skip destination pointer to next LCD row
	}
}


/*
void screen_draw_hexdigit(word x, word y, word v) {	// byte v	// ... but we are always passing 16-bit anyway!
	if (v <= 0x09)
		screen_draw_glyph(x  , y, (word)('0'+v));
	else if (v <= 0x0f)
		screen_draw_glyph(x  , y, (word)('A'+v-0x0a));
	else
		screen_draw_glyph(x  , y, (word)'?');
}


void screen_draw_hex8(word x, word y, word v) {	// byte v	// ... but we are always passing 16-bit anyway!
	screen_draw_hexdigit(x, y, (v >> 4)); x += FONT_WIDTH;
	screen_draw_hexdigit(x, y, (v & 0x0f));
}


void screen_draw_hex16(word x, word y, word v) {
	screen_draw_hexdigit(x, y, (v >> 12)      ); x += FONT_WIDTH;
	screen_draw_hexdigit(x, y, (v >>  8) & 0xf); x += FONT_WIDTH;
	screen_draw_hexdigit(x, y, (v >>  4) & 0xf); x += FONT_WIDTH;
	screen_draw_hexdigit(x, y, (v      ) & 0xf);
}
*/

/*
void draw_pchar(word x, word y, __far char *p) {
	while (*p != 0) {
		draw_glyph(x, y, (word)*p++);
		x += FONT_WIDTH;
		if (x >= SCREEN_WIDTH) {
			x = 0;
			y += FONT_HEIGHT;
		}
	}
}
*/

void screen_putchar(int c) {
	//int over;
	
	if ((c == '\r') || (c == '\n')) {
		screen_x = 0;
		screen_y += FONT_HEIGHT;
	} else if (c == 8) {
		if (screen_x >= FONT_WIDTH)
			screen_x -= FONT_WIDTH;
		else
			screen_x = 0;
	} else if (c == 9) {
		screen_x = ((screen_x >> 5) + 1) << 5;
	} else {
		screen_draw_glyph(screen_x, screen_y, (word)c);
		screen_x += FONT_WIDTH;
	}
	
	if (screen_x >= SCREEN_WIDTH) {
		screen_x -= SCREEN_WIDTH;
		screen_y += FONT_HEIGHT;
	}
	
	//if (screen_y+FONT_HEIGHT > SCREEN_HEIGHT) {
	//	over = (screen_y+FONT_HEIGHT) - SCREEN_HEIGHT;
	if (screen_y >= SCREEN_HEIGHT) {
		screen_scroll(FONT_HEIGHT);
		screen_y = SCREEN_HEIGHT - FONT_HEIGHT;
	}
}


//@FIXME: Not real printf. Just a way to output a pchar
void screen_printf(__far char *s) {
	char c;
	
	while(1) {
		c = *s++;
		if (c == 0) break;
		screen_putchar(c);
	}
}


#endif
