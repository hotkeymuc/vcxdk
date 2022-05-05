
//#include <stdio.h>
/*
typedef unsigned char byte;
typedef unsigned short word;
*/
//register int *foovar __asm__("r9");
/*
word foo(word a, word b) {
	if (a > 5) {
		return a - b;
	} else {
		return a + b;
	}
}
*/
/*
void bar(void) {
	__asm__("nop");
}
*/
void alert(__far char *text) {
	(void)text;	// Disable "unused" warning
	
	__asm__("push    $2, era");
	
	// Show alert
	__asm__("movd    $0x034191, (r1,r0)");	// Dunno what this param does
	__asm__("adduw   $-0x8, sp");
	__asm__("storw   r0, 0x4(sp)");
	__asm__("storw   r1, 0x6(sp)");
	
	//__asm__("movd    .str_htk, (r1,r0)");
	// Copy function parameter (r3,r2) to (r1, r0)
	__asm__("movw    r3, r1");
	__asm__("movw    r2, r0");
	__asm__("adduw   $0x10, r1");	// Add the cartridge ROM base address (0x100000)
	
	__asm__("storw   r0, 0(sp)");
	__asm__("storw   r1, 0x2(sp)");
	
	__asm__("movb    $0, r4");	// Dunno what this param does
	__asm__("movd    $0x084D40, (r3,r2)");	// Dunno what this param does
	__asm__("bal     (ra,era), 0x198CC4");	// show_info_popup_r1r0 (0x018CC4 + internal ROM offset 0x180000)
	
	__asm__("adduw   $0x8, sp");
	
	// Clean up
	__asm__("pop     $2, era");
	
}

int prompt(__far char *title, __far char *text) {
	(void)title;
	(void)text;
	
	__asm__("push    $2, era");
	
	// Show prompt
	__asm__("movd    $0x034191, (r1,r0)");	// Dunno what this param does...
	__asm__("push    $2, r0");
	
	//__asm__("movd    .str_hello, (r3,r2)");	// Use our own constant
	__asm__("adduw   $0x10, r3");	// Add the cartridge ROM base address (0x100000)
	//__asm__("movd    .str_htk, (r5,r4)");	// Use our own constant
	__asm__("adduw   $0x10, r5");	// Add the cartridge ROM base address (0x100000)
	
	__asm__("bal     (ra,era), 0x1805C4");	// prompt_yesno__title_r3r2__text_r5r4__sys5c4 (0x0005C4 + internal ROM offset 0x180000)
	__asm__("adduw   $0x4, sp");
	
	// Check the result in r0
	//__asm__("cmpb    $0x1, r0");	// 1 = YES, 0 = NO
	//__asm__("beq     .start");	// Back to start
	//__asm__(";beq     .end");	// Exit out
	
	// Clean up
	__asm__("pop     $2, era");
	
	// "return" statement intentionally omitted, because register r0 is already set and should remain
	
}

// Keep them 2-aligned, but keep in mind that they contain a trailing zero!
__far const char hello[] = "Hello there";
__far const char world[] = "World!!";
__far const char yes[] = "YES!!";
__far const char no[] = "NO!";

void main(void) {
	/*
	word a, b, c;
	
	printf("Hello world.\n");
	
	a = 4;
	b = 10;
	c = foo(a, b);
	//c = a * b;
	printf("%d", c);
	*/
	
	//alert("Hello.");
	alert(&hello);
	
	while(1) {
		if (prompt(&hello, &world) == 1)
			alert(&yes);
		else
			alert(&no);
	}
	
}
