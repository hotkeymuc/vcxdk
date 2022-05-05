#!/bin/sh
# Run make.bat using wine
wine cmd.exe /c make.bat test

#echo Disassembling using my own disasm...
#python3 ../cr16b_dasm/cr16b_dasm.py test.o

python3 ../../tools/cr16b_dasm/cr16b_asm.py --output test.bin --pad 8192 cart_header.asm test.s

#python3 ../../tools/cr16b_dasm/cr16b_dasm.py test.bin
