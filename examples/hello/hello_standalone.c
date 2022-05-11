/*
A stand-alone proof-of-concept test program.
It calls "widgets" in the firmware to show an alert and confirmation-prompt.
This was the first piece of code that managed to run on real hardware and which did evoke a reaction by the system.

Known issue:
	The dialogs won't display in main menu.
	
Fix:
	* Enter main menu
	* Select the "System" category
	* Start "File Manager"
	* Now press the "Cartridge" soft button to run the program


2022-05-06 Bernhard "HotKey" Slawik
*/



// Some trials agains VTech Genius Leader 8008 CX [de] firmware traps
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



#pragma set_options("-Wno-return-type")	// Suppress warning "control reaches end of non-void function", because we manually set R0
int confirm(__far char *title, __far char *text) {
	(void)title;
	(void)text;
	
	__asm__("push    $2, era");
	
	// Show prompt
	__asm__("movd    $0x034191, (r1,r0)");	// Dunno what this param does...
	__asm__("push    $2, r0");
	
	// Title parameter is in (r3,r2)
	//__asm__("movd    .str_hello, (r3,r2)");	// Set pointer of title
	__asm__("adduw   $0x10, r3");	// ...add the cartridge ROM base address (0x100000)
	
	// Text parameter is in (r5,r4)
	//__asm__("movd    .str_htk, (r5,r4)");	// Set pointer of text
	__asm__("adduw   $0x10, r5");	// ...add the cartridge ROM base address (0x100000)
	//XXX: __asm__("adduw   $0x10, r5");	// XXX ...add the RAM base address (not 00, 01, 02, 03, 04, 07, 08, 0f, 10, 18, 20)
	
	__asm__("bal     (ra,era), 0x1805C4");	// prompt_yesno__title_r3r2__text_r5r4__sys5c4 (0x0005C4 + internal ROM offset 0x180000)
	__asm__("adduw   $0x4, sp");
	
	// Check the result in r0
	//__asm__("cmpb    $0x1, r0");	// 1 = YES, 0 = NO
	//__asm__("beq     .start");	// Back to start
	
	// Clean up
	__asm__("pop     $2, era");
	
	// NOTE!
	// "return X" statement intentionally omitted, because register R0 is already set and should remain as-is.
	// So: ignore the warning "control reaches end of non-void function" (-Wno-return-type)
	
}
#pragma reset_options()



// Keep them 2-aligned, but keep in mind that they contain a trailing zero!
__far const char hello[] = "Hello";
__far const char world[] = "World!!";
__far const char yes[] = "YES!!";
__far const char no[] = "NO!";


void main(void) {
	//alert("Hello.");
	//alert(&hello);
	alert((__far char *)&hello);
	
	while(1) {
		if (confirm((__far char *)&hello, (__far char *)&world) == 1)
			alert((__far char *)&yes);
		else
			alert((__far char *)&no);
	}
	
}
