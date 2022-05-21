
typedef unsigned char byte;
typedef unsigned short word;

void put(const char *s) {
}

void foo(int x, int y) {
	if (x < y) {
		put("smaller");
	} else {
		put("bigger");
	}
}

const byte life = 42;

int main(void) {
	int a;
	int b;
	int i;
	
	a = life;
	b = life * 99;
	for(i = 0; i < 10; i++) {
		a = a * 3;
	}
	
	put("Hello world");
	foo(b, a);
}
