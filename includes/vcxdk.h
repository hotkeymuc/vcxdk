#ifndef __VCXDK_H
#define __VCXDK_H

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned long int dword;
typedef unsigned short size_t;

//#include "memory.h"
//#include "screen.h"
//#include "keyboard.h"
//#include "ui.h"

/*
__far void *CARTRIDGE_ROM_POINTER(__far void *p) {
	// Change the given pointer to point to ROM space
	
	__asm__("adduw   $0x10, r3");	// Add the cartridge ROM base address (0x100000)
	__asm__("storw	r3,2(sp)");
	return p;
}
*/

//#define mem(x) *(unsigned char *)(x)


#endif
