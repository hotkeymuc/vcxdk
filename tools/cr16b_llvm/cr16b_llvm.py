"""

There is no open source version of a CR16B compiler, yet. (There is only the proprietary CR16 Toolset for Windows)

Idea:
	* Create LLVM IR code (e.g. via clang)
		clang -S -emit-llvm foo.c
		clang -cc1 foo.c -emit-llvm
	* Transform IR instructions into CR16B assembly
	* Compile/link using cr16b_asm.py

Tricky:
	Convert assignments ("%0", "%1", "%2", ...) into registers/stack



"""

def put(t):
	print(t)



if __name__ == '__main__':
	
	pass