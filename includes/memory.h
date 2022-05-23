#ifndef __MEMORY_H
#define __MEMORY_H

/*
Memory Utilities for CR16B CPU / VTech CX series

*/


/*
This alters the given __far pointer to point into ROM space.
This is done by adding 0x10 to the "high" address byte.
Use this e.g. to pass constant strings from ROM to system functions.
	CARTRIDGE_ROM_POINTER(&"This is a string in ROM")
*/
__far void *CARTRIDGE_ROM_POINTER(__far void *p) {
	
	// This assembly part is highly dependent on the compiler output (and memory access model)!
	// Check the .s file to see if this hack actually blends in correctly!
	
	#ifdef CRCC_OPT
		// For "-O" optimization (variables in registers)
		__asm__("adduw   $0x10, r1");	// Add the cartridge ROM base address (0x100000)
		// r1 is already the return value
	#else
		// For no optimization (variables on heap)
		__asm__("adduw   $0x10, r3");	// Add the cartridge ROM base address (0x100000)
		__asm__("storw	r3,2(sp)");	// Store it back to local variable
	#endif
	
	// Return it
	return p;
}

// Helper for accessing memory
#define mem(x) *(byte *)(x)


#endif
