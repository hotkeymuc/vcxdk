#ifndef __VCXDK_H
#define __VCXDK_H

typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned long int dword;
typedef unsigned short size_t;

#define NULL (void *)0
#define true 1
#define false 0

//#define CTRL_REG *((volatile short *)0xff00)
//#define mem(x) *(byte *)(x)


/*

As of CR16C A.5: String and float constants MUST belocated in first 64K of memory space.
But cartridges are mounted at 0x100000, which is far.

To circumvent this, you can use ROM_POINTER("foo") to convert it into the correct base location.
This is done by adding 0x10 to the "high" address byte.

Use this e.g. to pass constant strings from ROM to system functions.
	ROM_POINTER("This is a string in ROM")

*/


//#define ROM_POINTER(p) p

__far void *ROM_POINTER(__far void *p) {
	
	// This assembly part is highly dependent on the compiler output (and memory access model)
	// Check the produced .s file to see if this hack actually blends in correctly!
	
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
}

//#include "memory.h"
//#include "screen.h"
//#include "keyboard.h"
//#include "ui.h"


#endif
