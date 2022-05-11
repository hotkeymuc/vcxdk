#ifndef __MEMORY_H
#define __MEMORY_H

__far void *ROM_POINTER(__far void *p) {
	// Alter the given __far pointer to point to ROM space
	
	__asm__("adduw   $0x10, r3");	// Add the cartridge ROM base address (0x100000)
	__asm__("storw	r3,2(sp)");
	return p;
}

#define mem(x) *(unsigned char *)(x)


#endif
