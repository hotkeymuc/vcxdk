#ifndef __VCXDK_H
#define __VCXDK_H

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned long int dword;
typedef unsigned short size_t;

#define NULL (void *)0
#define true 1
#define false 0

//#include "memory.h"
//#include "screen.h"
//#include "keyboard.h"
//#include "ui.h"

/*
__far void *CARTRIDGE_ROM_POINTER(__far void *p) {
	
	// This assembly part is highly dependent on the compiler output (and memory access model)!
	// Check the .s file to see if this hack actually blends in correctly!
	
	#ifdef CRCC_OPT
		// For "-O" optimization (variables in registers)
		//__asm__("adduw   $0x10, r1");	// Add the cartridge ROM base address (0x100000)
		__asm__("orw   $0x10, r1");	// Add the cartridge ROM base address (0x100000)
		// r1 is already the return value
	#else
		// For no optimization (variables on heap)
		//__asm__("adduw   $0x10, r3");	// Add the cartridge ROM base address (0x100000)
		__asm__("orw   $0x10, r3");	// Add the cartridge ROM base address (0x100000)
		__asm__("storw	r3,2(sp)");	// Store it back to local variable
	#endif
	
	// Return it
	return p;
*/


#endif
