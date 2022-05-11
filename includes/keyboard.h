#ifndef __KEYBOARD_H
#define __KEYBOARD_H
/*
Genius Leader 8008 CX (german) firmware keyboard hook

This accesses memory addresses 0x78c0-0x78cb


78C0 = Keyboard state!
	78C3-78C9: keyboard buffer (4 x 16 bit), stores scancodes
	78CF: current IN index in buffer; used by ROM (sys3c8)	037B2C:	1F D8 CF 78	D81F 78CF	storb   r0, 0x078CF
	78D0: current OUT index in buffer; used by ROM (sys3c8)	037B28:	1F D8 D0 78	D81F 78D0	storb   r0, 0x078D0
	
	78CB: current SCAN CODE (FF if none)
		
		5E = SoftKey: "E-Mail"
		5D = SoftKey 5 "Kunststudio"
		5C = "3"
		5B = "E"
		5A = "S"
		59 = "X"
		58 = ANSWER/PRINT
		
		56 = SoftKey "System"
		55 = SoftKey 6 "Hausaufgabenhilfe"
		54 = "2"
		53 = "W"
		52 = "A"
		51 = "Y" (de)
		50 = PLAYER/BOOKMARK
		
		
		4E = SoftKey "MagiCam"
		4D = SoftKey "Demo"
		4C = "1"
		4B = "Q"
		4A = ?unused?
		49 = ?unused?
		48 = LEVEL/SYMBOL
		
		46 = SoftKey "Kassette"
		45 = SoftKey "Drucker"
		44 = ESC
		43 = TAB
		42 = CAPSLOCK
		41 = SHIFT LEFT
		40 = PLAYER1/HELP
		
		
		3E = INSERT/DELETE
		3D = "'" (de) / "`" / "^"
		3C = "Ss" (de) / "?" / "\\"
		3B = "Ue" (de)
		3A = "Oe" (de)
		39 = "-" / "_"
		38 = SHIFT RIGHT
		
		36 = ENTER
		35 = "+" / "*" / "~"
		34 = "0"
		33 = "P"
		32 = "L"
		31 = "." / ":" / ">"
		30 = CURSOR RIGHT / Player2 / End
		
		
		2E = BACKSPACE
		2D = "Ae" (de)
		2C = "9"
		2B = "O"
		2A = "K"
		29 = ","/";", "<"
		28 = CURSOR DOWN / Page Down
		
		26 = TouchPad Button LEFT
		25 = CURSOR UP / Page Up
		24 = "8"
		23 = "I"
		22 = "J"
		21 = "M"
		20 = CURSOR LEFT / Home
		
		
		1E = Touchpad Button RIGHT
		1D = SoftKey 4 "Logik & Spiele"
		1C = "7"
		1B = "U"
		1A = "H"
		19 = "N"
		18 = REPEAT
		
		16 = SoftKey 2 "Mathematik"
		15 = SoftKey 1 "Wortspiele"
		14 = "6"
		13 = "Z" (de)
		12 = "G"
		11 = "B"
		10 = ALT
		
		
		0E = POWER ON
		0D = POWER OFF
		0C = "5"
		0B = "T"
		0A = "F"
		09 = "V"
		08 = SPACE
		
		06 = SoftKey 6 "Computerpraxis"
		05 = SoftKey 3 "Quiz-Fragen"
		04 = "4"
		03 = "R"
		02 = "D"
		01 = "C"
		00 = CONTROL LEFT
		
		FF=none
		
	78F4 used by ROM: 037EAA:	1F D8 F4 78	D81F 78F4	storb   r0, 0x078F4
	78D1 used by ROM: 037EAE:	1F D8 D1 78	D81F 78D1	storb   r0, 0x078D1
	

	7960: used by ROM (sys5a0)
	7962: used by ROM (sys5a0)


2022-05-10 Bernhard "HotKey" Slawik
*/

// Addresses for 8008 CX (de) firmware
#define KEYBOARD_BUFFER 0x78c3
#define KEYBOARD_BUFFER_IN 0x78cf
#define KEYBOARD_BUFFER_OUT 0x78d0
#define KEYBOARD_BUFFER_SIZE 4
#define KEYBOARD_CURRENT_SCANCODE 0x78cb


#define KEY_NONE -1
#define KEY_SHIFT_LEFT 0x00
#define KEY_SHIFT_RIGHT 0x00
#define KEY_CAPS_LOCK 0x00
#define KEY_CONTROL 0x00
#define KEY_ALT 0x00
#define KEY_BACKSPACE 0x08
#define KEY_INSERT 0x00
#define KEY_TAB 0x09
#define KEY_ENTER 0x0a
#define KEY_ESCAPE 0x1b
#define KEY_POWER_ON 0x00
#define KEY_POWER_OFF 0x00
#define KEY_LEVEL 0x00
#define KEY_PLAYERS 0x00
#define KEY_PLAYER_1 0x00
#define KEY_PLAYER_2 0x00
#define KEY_HELP 0x00
#define KEY_REPEAT 0x00
#define KEY_ANSWER 0x00
#define KEY_CURSOR_UP 0x00
#define KEY_CURSOR_DOWN 0x00
#define KEY_CURSOR_LEFT 0x00
#define KEY_CURSOR_RIGHT 0x00
#define KEY_MOUSE_BUTTON_LEFT 0x00
#define KEY_MOUSE_BUTTON_RIGHT 0x00
#define KEY_SOFT_1 0x00
#define KEY_SOFT_2 0x00
#define KEY_SOFT_3 0x00
#define KEY_SOFT_4 0x00
#define KEY_SOFT_5 0x00
#define KEY_SOFT_6 0x00
#define KEY_SOFT_CARTRIDGE 0x00
#define KEY_SOFT_PRINTER 0x00
#define KEY_SOFT_DEMO 0x00
#define KEY_SOFT_MAGICAM 0x00
#define KEY_SOFT_SYSTEM 0x00
#define KEY_SOFT_EMAIL 0x00

#define KEY_BREAK 0x00
#define KEY_DELETE 0x00
#define KEY_SYMBOL 0x00
#define KEY_BOOKMARKS 0x00
#define KEY_SYSTEM 0x00
#define KEY_PRINT 0x00
#define KEY_PAGE_UP 0x00
#define KEY_PAGE_DOWN 0x00
#define KEY_HOME 0x00
#define KEY_END 0x00

const char KEY_MAP[2][6][16] = {
	// Normal
	{
		{KEY_CONTROL, 'c', 'd', 'r', '4', KEY_SOFT_3, KEY_SOFT_6,	KEY_NONE,	' ', 'v', 'f', 't', '5', KEY_POWER_OFF, KEY_POWER_ON,	KEY_NONE},
		{KEY_ALT, 'b', 'g', 'z', '6', KEY_SOFT_1, KEY_SOFT_2,	KEY_NONE,	KEY_REPEAT, 'n', 'h', 'u', '7', KEY_SOFT_4, KEY_MOUSE_BUTTON_RIGHT,	KEY_NONE},
		{KEY_CURSOR_LEFT, 'm', 'j', 'i', '8', KEY_CURSOR_UP, KEY_MOUSE_BUTTON_LEFT,	KEY_NONE,	KEY_CURSOR_DOWN, ',', 'k', 'o', '9', 'ä', KEY_BACKSPACE,	KEY_NONE},
		{KEY_CURSOR_RIGHT, '.', 'l', 'p', '0', '+', KEY_ENTER,	KEY_NONE,	KEY_SHIFT_RIGHT, '-', 'ö', 'ü', 'ß', '\'', KEY_INSERT,	KEY_NONE},
		{KEY_HELP, KEY_SHIFT_LEFT, KEY_CAPS_LOCK, KEY_TAB, KEY_ESCAPE, KEY_SOFT_PRINTER, KEY_SOFT_CARTRIDGE,	KEY_NONE,	KEY_LEVEL, KEY_NONE, KEY_NONE, 'q', '1', KEY_SOFT_DEMO, KEY_SOFT_MAGICAM,	KEY_NONE},
		{KEY_PLAYERS, 'y', 'a', 'w', '2', KEY_SOFT_6, KEY_SOFT_SYSTEM,	KEY_NONE,	KEY_ANSWER, 'x', 's', 'e', '3', KEY_SOFT_5, KEY_SOFT_EMAIL,	KEY_NONE},
	},
	// Shift
	{
		{KEY_CONTROL, 'C', 'D', 'R', '$', KEY_SOFT_3, KEY_SOFT_6,	KEY_NONE,	' ', 'V', 'F', 'T', '%', KEY_POWER_OFF, KEY_POWER_ON,	KEY_NONE},
		{KEY_ALT, 'B', 'G', 'Z', '&', KEY_SOFT_1, KEY_SOFT_2,	KEY_NONE,	KEY_REPEAT, 'N', 'H', 'U', '/', KEY_SOFT_4, KEY_MOUSE_BUTTON_RIGHT,	KEY_NONE},
		{KEY_HOME, 'M', 'J', 'I', '(', KEY_PAGE_UP, KEY_MOUSE_BUTTON_LEFT,	KEY_NONE,	KEY_PAGE_DOWN, ';', 'K', 'O', ')', 'Ä', KEY_BACKSPACE,	KEY_NONE},
		{KEY_END, ':', 'L', 'P', '=', '*', KEY_ENTER,	KEY_NONE,	KEY_SHIFT_RIGHT, '_', 'Ö', 'Ü', '?', '`', KEY_DELETE,	KEY_NONE},
		{KEY_PLAYER_1, KEY_SHIFT_LEFT, KEY_CAPS_LOCK, KEY_TAB, KEY_BREAK, KEY_SOFT_PRINTER, KEY_SOFT_CARTRIDGE,	KEY_NONE,	KEY_SYMBOL, KEY_NONE, KEY_NONE, 'Q', '!', KEY_SOFT_DEMO, KEY_SOFT_MAGICAM,	KEY_NONE},
		{KEY_BOOKMARKS, 'Y', 'A', 'W', '"', KEY_SOFT_6, KEY_SOFT_SYSTEM,	KEY_NONE,	KEY_PRINT, 'X', 'S', 'E', '§', KEY_SOFT_5, KEY_SOFT_EMAIL,	KEY_NONE},
	}
}
;

char scancode_to_char(unsigned char scancode, unsigned char modifiers) {
	// Convert given scancode (and mofidiers) to ASCII character
	
	__far char *p;
	char c = 0;
	
	if (scancode >= 0x60) return KEY_NONE;
	
	//@FIXME: ROM-addresses must be manually hacked to point to the correct code segment!
	p = (__far char *)&KEY_MAP;
	__asm__("adduw   $0x10, r0");	// Add the cartridge ROM base address (0x100000)
	__asm__("storw	r0,4(sp)");
	
	// Use scancode DIRECTLY as absolute index (0x00 - 0x5f)
	p += scancode;
	
	//@TODO: Apply modifiers
	if (modifiers > 0) {
		p += (6 * 16);
	}
	
	c = *p;
	
	
	return c;
}

unsigned char get_current_scancode(void) {
	// Return the currently depressed scancode
	
	return *(unsigned char *)(KEYBOARD_CURRENT_SCANCODE);
}

unsigned char key_available(void) {
	// Return 1 if a key is in buffer, else 0
	
	if (*(unsigned char *)KEYBOARD_BUFFER_OUT != *(unsigned char *)KEYBOARD_BUFFER_IN) {
		return 1;
	}
	return 0;
}

char getchar(void) {
	// Block until key is pressed, then consume that scancode and return it as ASCII character
	
	unsigned char scancode;
	unsigned char modifiers;
	unsigned char index;
	
	// Wait for buffer to hold something
	// while (*(unsigned char *)(KEYBOARD_BUFFER_IN) == *(unsigned char *)(KEYBOARD_BUFFER_OUT)) { }
	index = *(unsigned char *)(KEYBOARD_BUFFER_OUT);
	while (*(unsigned char *)KEYBOARD_BUFFER_IN == index) {
		// Wait for BUFFER_IN to increment
	}
	
	// Increment BUFFER_OUT
	//@FIXME: Modulo gets compiled to "_fast_rem" which I don't have, yet.
	//*(unsigned char *)(KEYBOARD_BUFFER_OUT) = (*(unsigned char *)(KEYBOARD_BUFFER_OUT) + 1) % KEYBOARD_BUFFER_SIZE;
	index ++;
	if (index >= KEYBOARD_BUFFER_SIZE)
		index -= KEYBOARD_BUFFER_SIZE;
	
	// Fetch scancode
	scancode = *(unsigned char *)(KEYBOARD_BUFFER + (index * 2));
	modifiers = *(unsigned char *)(KEYBOARD_BUFFER + (index * 2) + 1);
	
	// Write incremented BUFFER_OUT
	*(unsigned char *)(KEYBOARD_BUFFER_OUT) = index;
	
	// Convert to char
	return scancode_to_char(scancode, modifiers);
}

#endif
