#!/bin/sh

# Run make.bat using wine which calls the CR16B toolset C compiler
wine cmd.exe /c make.bat test

#echo Disassembling using my own disasm...
#python3 ../cr16b_dasm/cr16b_dasm.py test.o

# Turn the generated assembly into a binary file
python3 ../../tools/cr16b_asm/cr16b_asm.py --output test.bin --pad 8192 cart_header.asm test.s

# Disassemble the result to check
#python3 ../../tools/cr16b_dasm/cr16b_dasm.py test.bin
