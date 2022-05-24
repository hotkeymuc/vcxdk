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
	putchar('\n');
}

//void printf(__far const char *format, ...) { }

#define CURSOR_BLINK
__far char *gets(__far char *s) {
	int c;
	//char *ps;
	byte l;
	#ifdef CURSOR_BLINK
	word timeout;
	byte blinkframe;
	blinkframe = 0;
	#endif
	
	//ps = s;
	l = 0;
	c = 0;
	
	while(c != 10) {
		
		#ifdef CURSOR_BLINK
			// Blink (non-blocking)
			screen_draw_glyph(screen_x, screen_y, (blinkframe==0) ? 219 : 176);
			
			c = 0xff;
			timeout = 0x8000;
			while ((timeout > 0) && (key_available() == 0)) {
				timeout--;
			}
			if (key_available() > 0) {
				c = getchar();
				blinkframe = 0;
				// if echo
				screen_draw_glyph(screen_x, screen_y, ' ');
			} else {
				blinkframe = 1-blinkframe;
			}
			
		#else
			// Simple (blocking)
			screen_draw_glyph(screen_x, screen_y, '_');
			c = getchar();
			screen_draw_glyph(screen_x, screen_y, ' ');
		#endif
		
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
