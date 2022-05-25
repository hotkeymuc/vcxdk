#ifndef __STDIOMIN_H
#define __STDIOMIN_H

/*
Barebones input/output

*/

#include <vcxdk.h>
#include <keyboard.h>
#include <screen.h>


// Use screen
#define clear() screen_clear()
#define putchar(c) screen_putchar(c)
#define printf(c) screen_printf(c)
#define printf_far(c) screen_printf_far(c)


void puts(char* s) {
	printf(s);
	
	// Trailing new line as per spec
	putchar('\n');
}
void puts_far(__far char* s) {
	printf_far(s);
	
	// Trailing new line as per spec
	putchar('\n');
}

//void printf(__far const char *format, ...) { }

#define CURSOR_BLINK

//__far char *gets(__far char *s) {
char *gets(char *s) {
	int c;
	//char *ps;
	word l;
	
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
			#ifdef FONT_FULL_8BIT
				screen_draw_glyph(screen_x, screen_y, (blinkframe==0) ? 219 : ' ');
			#else
				screen_draw_glyph(screen_x, screen_y, (blinkframe==0) ? '_' : ' ');
			#endif
			
			c = 0xff;
			timeout = 0x7800;
			while ((timeout > 0) && (key_available() == 0)) {
				timeout--;
			}
			if (key_available() > 0) {
				c = getchar();
				blinkframe = 0;
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
			} else if (c == 27) {
				// Cancel
				//s -= l;
				break;
				
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



#endif
