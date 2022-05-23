#!/bin/bash

INPUT_BASENAME=monitor
INPUT_FILENAME=${INPUT_BASENAME}.c
OUTPUT_FILENAME=${INPUT_BASENAME}.bin

CR16TOOLSET_PATH=../../tools/CR16toolset
CR16BASM_PATH=../../tools/cr16b_asm
INCLUDES_PATH=../../includes
HEADER_FILENAME=${INCLUDES_PATH}/cart_header.asm
BINARY_SIZE=8192


# Clean
echo Cleaning up...
[ -e ${INPUT_BASENAME}.err ] && rm ${INPUT_BASENAME}.err
[ -e ${INPUT_BASENAME}.o ] && rm ${INPUT_BASENAME}.o
[ -e ${INPUT_BASENAME}.s ] && rm ${INPUT_BASENAME}.s


# Compile
echo Compiling \"${INPUT_FILENAME}\" using crcc...

#	CompactRISC CR16 C Compiler Release 3.1 (revision 5)
#	Usage: crcc [ [-flag] | [file] | [@argfile]  ] ... 
#	              @argfile:  Read all, or part, of the flags from argfile
#	                    -V:  Print compiler version
#	           -o filename:  Specify an output file name
#	                    -c:  Compile but do not link
#	                    -g:  Generate symbolic debugging information
#	                    -S:  Generate assembly code only
#	                 -S -n:  Embed C source lines as comments in assembly file
#	                    -O:  Optimize for speed
#	                   -Os:  Optimize for space
#	                   -ON:  Optimize for speed and perform loop unrolling
#	                   -Oi:  Optimize and treat all globals as volatile
#	                -sbrel:  Use static base register optimization
#	               -J[1|2]:  Set largest alignment within structures
#	              -KB[1|2]:  Set bus width (alignment of stack)
#	         -fshort-enums:  Select the shortest size for enumeration type
#	    -finline-functions:  Integrate all simple functions into their callers
#	-fkeep-inline-functions: Keep body of inline functions
#	       -ffixed-r[7-13]:  Do not use register r<n> (e.g. -ffixed-r10)
#	               -mcr16c:  Generate code for CR16C standard mode (default)
#	             -mcr16csr:  Generate code for CR16C compatible mode
#	           -mcr16cplus:  Generate code for CR16CPlus
#	               -msmall:  Generate code for CR16B small memory model
#	               -mlarge:  Generate code for CR16B large memory model
#	             -mall-far:  Treat all variables as far
#	                -mfar2:  Allocate far variables in the whole memory space
#	                         (CR16B and CR16CPlus only)
#	                 -ansi:  Accept only strict ANSI C programs
#	               -Wextra:  Warn about non-obvious potential problems
#	         -Wno-<option>:  Disable warning <option>
#	                    -w:  No warning diagnostics
#	                    -Q:  Error checking only
#	                    -v:  Verbose mode (show compilation stages)
#	                   -vn:  Verbose mode without actually executing
#	                    -z:  Dump errors and warnings into <file>.err
#	         -zn<filename>:  Dump errors and warnings into <filename>
#	Preprocessor flags: 
#	                    -E:  Run cpp only, redirect output to stdout
#	                    -P:  Run cpp only, redirect output to <file>.i
#	        -Dsymbol[=def]:  Define cpp symbol
#	              -Usymbol:  Undefine cpp symbol
#	                 -Idir:  Specify additional directory for included files
#	                    -M:  Generate makefile dependencies
#	
#	Linking flags:
#	                -lname:  Specify a standard library for the linker
#	          -KFemulation:  Use floating point emulation library
#	                 -Ldir:  Specify the libraries directory
#	    -W[p|c|a|l],option:  Pass option to different stages
#	                   -Wp:     preprocessor
#	                   -Wc:     compiler
#	                   -Wa:     assembler
#	                   -Wl:     linker

# cc.arg:
#	-DNATIONAL_COMPILER
#	-DFSYS=20000000UL
#	-DBAUD_RATE=115200UL
#	-DUART_FRAME=N81
#	-DSW_FLOW_CTRL
#	-DnoHW_FLOW_CTRL
#	-Oi
#	-Os
#	-g
#	-z
#	-n
#	-S
#	-J1

# crcc @cc.arg -v -mlarge -Dfoo=bar test.c
# crcc @cc.arg -msmall -Wextra -S test.c
# crcc @cc.arg -mlarge -Wextra -S test.c
# crcc @cc.arg -mlarge -Wextra %INPUTNAME%.c
# crcc -mlarge -Wextra %INPUTNAME%.c

# Wine passes exported environment variables over
# Create a backslash-version of the toolset path
export CRDIR=${CR16TOOLSET_PATH//\//\\}

# Call the compiler using Wine
#wine ${CR16TOOLSET_PATH}/crcc.exe -mlarge -Wextra -I${INCLUDES_PATH} -c -S -n ${INPUT_FILENAME}
#wine ${CR16TOOLSET_PATH}/crcc.exe -mlarge -O -DCRCC_OPT -I${INCLUDES_PATH} -c -S -n ${INPUT_FILENAME}
wine ${CR16TOOLSET_PATH}/crcc.exe -mlarge -I${INCLUDES_PATH} -c -S -n ${INPUT_FILENAME}

# Check result, stop if something went wrong
CRCC_RESULT=$?
if [ $CRCC_RESULT -ne 0 ]; then
	echo Compilation failed. Stopping make.
	exit $CRCC_RESULT
fi


#echo Disassembling using my own disasm...
#python3 ../cr16b_dasm/cr16b_dasm.py test.o


# Assemble binary
echo Assembling \"${OUTPUT_FILENAME}\"...
# Turn the generated assembly into a binary file
#python3 ${CR16BASM_PATH}/cr16b_asm.py --verbose --stats --output ${INPUT_BASENAME}.bin cart_header.asm ${INPUT_BASENAME}.s
python3 ${CR16BASM_PATH}/cr16b_asm.py --stats --output ${OUTPUT_FILENAME} --pad ${BINARY_SIZE} ${HEADER_FILENAME} ${INPUT_BASENAME}.s


# Disassemble the result to check
#python3 ../../tools/cr16b_dasm/cr16b_dasm.py test.bin


echo Finished.
