#ifndef __STDIOMIN_H
#define __STDIOMIN_H

/*
Barebones input/output

*/

#include <vcxdk.h>
#include <screen.h>
#include <keyboard.h>


// Use screen
#define putchar(c) screen_putchar(c)
#define printf(c) screen_printf(c)
#define clear() screen_clear()


void puts(__far char* s) {
	printf(s);
	
	// Trailing new line as per spec
	screen_putchar('\n');
	putchar('\n');
}

//void printf(__far const char *format, ...) { }

char *gets(char *s) {
	int c;
	//char *ps;
	byte l;
	
	//ps = s;
	l = 0;
	c = 0;
	while(c != 10) {
		
		// if echo
		screen_draw_glyph(screen_x, screen_y, '_');
		
		c = getchar();
		
		// if echo
		screen_draw_glyph(screen_x, screen_y, ' ');
		
		if ((c != 0xff) && (c != 0x00)) {
			
			if (c == 8) {
				if (l > 0) {
					// if echo
					putchar(8);
					
					s--;
					l--;
				}
			} else {
				// if echo
				putchar(c);
				
				*s++ = c;
				l++;
			}
		}
	}
	// Terminate
	*s++ = 0;
	
	return s;
}

void printf_x(word v) {	// byte v	// ... but we are always passing 16-bit anyway!
	if (v <= 0x09)
		putchar((int)('0'+v));
	else if (v <= 0x0f)
		putchar((int)('A'+v-0x0a));
	else
		putchar((int)'?');
}
void printf_x2(word v) {	// byte v	// ... but we are always passing 16-bit anyway!
	printf_x(v >> 4);
	printf_x(v & 0x0f);
}
void printf_x4(word v) {
	printf_x(v >> 12);
	printf_x((v >> 8) & 0x0f);
	printf_x((v >> 4) & 0x0f);
	printf_x(v & 0x0f);
}

/*
//void memcpy(void* dst_addr, const void* src_addr, size_t count) {
void memcpy(__far byte *dst_addr, __far byte *src_addr, word count) {
	//__far byte *ps;
	//__far byte *pd;
	
	//@TODO: Use Opcode for faster copy!!!
	//@TODO: Copy 16bits at once
	//ps = src_addr;
	//pd = dst_addr;
	while(count > 0) {
		*(byte *)dst_addr++ = *(byte *)src_addr++;
		count --;
	}
}

//void memset(void* addr, byte b, size_t count) {
void memset(__far byte *addr, byte b, word count) {
	while(count > 0) {
		*addr++ = b;
		count--;
	}
}
*/

#endif
