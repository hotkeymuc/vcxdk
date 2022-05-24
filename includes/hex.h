#ifndef __HEX_H
#define __HEX_H

/*
Some simple hex utils
*/

//#define HEX_USE_DUMP	// Include a "real" hexdump

byte hexDigit(byte c) {
	if (c < 10)
		return ('0'+c);
	return 'A' + (c-10);
}


void printf_x(word v) {	// byte v	// ... but we are always passing 16-bit anyway!
	if (v <= 0x09)
		putchar((int)('0'+v));
	else if (v <= 0x0f)
		putchar((int)('A'+v-0x0a));
	else
		putchar((int)'?');
}
void printf_x2(word v) {	// byte v	// ... but we are always passing 16-bit anyway!
	printf_x(v >> 4);
	printf_x(v & 0x0f);
}
void printf_x4(word v) {
	printf_x(v >> 12);
	printf_x((v >> 8) & 0x0f);
	printf_x((v >> 4) & 0x0f);
	printf_x(v & 0x0f);
}


byte parse_hexDigit(byte c) {
	if (c > 'f') return 0;
	
	if (c < '0') return 0;
	if (c <= '9') return (c - '0');
	
	if (c < 'A') return 0;
	if (c <= 'F') return (10 + c - 'A');
	
	if (c < 'a') return 0;
	return (10 + c - 'a');
}


word hextown(__far char *s, byte n) {
	byte i;
	word r;
	char c;
	
	r = 0;
	for(i = 0; i < n; i++) {
		c = *s++;
		if (c < '0') break;	// Break at zero char and any other non-ascii
		r = (r << 4) + (word)parse_hexDigit(c);
	}
	return r;
}

byte hextob(__far char *s) {
	return (byte)hextown(s, 2);
}

word hextow(__far char *s) {
	return hextown(s, 4);
}

#endif
