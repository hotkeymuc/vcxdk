#ifndef __STDLIBMIN_H
#define __STDLIBMIN_H

//#include <stdlib.h>	// for atoi()
int atoi(const char *a) {
	int i;
	i = 0;
	while (*a >= '0') {
		i = i*10 + (word)((*a++) - '0');
	}
	return i;
}


#endif
