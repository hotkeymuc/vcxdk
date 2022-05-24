/*
Hello VCXDK

A "Hello world" using frame buffer access.

2022-05-06 Bernhard "HotKey" Slawik
*/


#include <vcxdk.h>
//#include <stdio.h>
//#include <memory.h>
#include <screen.h>
//#include <keyboard.h>
//#include <ui.h>


void main(void) {
	//char c;
	
	screen_clear();
	
	//draw_pchar(0, 0, CARTRIDGE_ROM_POINTER("Hello VCXDK!"));
	//puts(CARTRIDGE_ROM_POINTER("Hello VCXDK!"));
	//puts("Hello VCXDK!");
	screen_printf("Hello VCXDK!");
	
	//c = getchar();
}
