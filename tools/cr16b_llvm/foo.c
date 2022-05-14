
typedef unsigned char byte;
typedef unsigned short word;

void put(const char *s) {
}
void foo(word x, word y) {
	if (x < y) {
		put("smaller");
	} else {
		put("bigger");
	}
}

const byte life = 42;

int main(void) {
	word a;
	word b;
	
	a = life;
	b = a * 3;
	
	put("Hello world");
	foo(b, a);
}
