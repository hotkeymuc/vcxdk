#ifndef __STRINGMIN_H
#define __STRINGMIN_H

//int strlen(__far const char *c) {
int strlen(const char *c) {
	int l;
	l = 0;
	while (*c++ != 0)  {
		l++;
	}
	return l;
}


byte strcmp_far(__far const char *cs, __far const char *ct) {
	while ((*cs != 0) && (*ct != 0)) {
		if (*cs++ != *ct++) return 1;
	}
	if (*cs != *ct) return 1;
	return 0;
}

byte stricmp1(char a, char b) {
	//putchar('[');putchar(a);putchar(b);
	if ((a >= 'a') && (a <= 'z')) a -= ('a' - 'A');
	if ((b >= 'a') && (b <= 'z')) b -= ('a' - 'A');
	if (a == b) {
		//putchar('0');putchar(']');
		return 0;
	}
	//putchar('1');putchar(']');
	return 1;
}
byte stricmp_far(__far const char *cs, __far const char *ct) {
	while ((*cs != 0) && (*ct != 0)) {
		if (stricmp1(*cs++, *ct++)) return 1;
	}
	if (stricmp1(*cs, *ct)) return 1;
	return 0;
}


/*
//void memcpy(void* dst_addr, const void* src_addr, size_t count) {
void memcpy_far(__far byte *dst_addr, __far byte *src_addr, word count) {
	//__far byte *ps;
	//__far byte *pd;
	
	//@TODO: Use Opcode for faster copy!!!
	//@TODO: Copy 16bits at once
	//ps = src_addr;
	//pd = dst_addr;
	while(count > 0) {
		*(byte *)dst_addr++ = *(byte *)src_addr++;
		count --;
	}
}

//void memset(void* addr, byte b, size_t count) {
void memset_far(__far byte *addr, byte b, word count) {
	while(count > 0) {
		*addr++ = b;
		count--;
	}
}
*/

#endif
