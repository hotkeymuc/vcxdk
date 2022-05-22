#ifndef __STRINGMIN_H
#define __STRINGMIN_H

//#include <string.h>	// For strcmp

//int strlen(__far const char *c) {
int strlen(const char *c) {
	int l;
	l = 0;
	while (*c++ != 0)  {
		l++;
	}
	return l;
}


byte strcmp(__far const char *cs, __far const char *ct) {
	while ((*cs != 0) && (*ct != 0)) {
		if (*cs++ != *ct++) return 1;
	}
	if (*cs != *ct) return 1;
	return 0;
}

byte stricmp1(char a, char b) {
	if ((a >= 'a') && (a <= 'z')) a -= ('a' - 'A');
	if ((b >= 'a') && (b <= 'z')) b -= ('a' - 'A');
	if (a != b) return 1;
	return 0;
}
byte stricmp(__far const char *cs, __far const char *ct) {
	while ((*cs != 0) && (*ct != 0)) {
		if (stricmp1(*cs++, *ct++)) return 1;
	}
	if (stricmp1(*cs, *ct)) return 1;
	return 0;
}

#endif
