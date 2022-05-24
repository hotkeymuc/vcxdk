#!/bin/bash

# VCXDK Master Make Script
# ========================
#
#
#	ECHO_COMMANDS (default)
#		Show the command that is run in the make toolchain
#	
#	CRT_FILENAME
#		If set: Use different CRT assembly file than default
#	
#	BINARY_SIZE
#		If set: Pad binary file to given size (in bytes)
#	
#	CRCC_OPTIMIZE
#		If set: Activate CRCC "-O" option, generating optimized assembly code
#	
#	CR16BASM_VERBOSE
#		If set: Make CR16B be verbose and show stats
#

#echo " ...  ......      .....  ................................................. "
#echo "....   ......    .....                                                 ...."
#echo "....   .......  .....  ........... .......... .........  .....  .....  ...."
#echo "....    ...... ......     ....    .....      .....      .....  .....   ...."
#echo "....     ...........     ....    .........  .....      ............    ...."
#echo "....      .........     ....    .....       .....     .....  .....     ...."
#echo "....       .......     ....     ..........  ........ .....  .....      ...."
#echo "....                                                                   ...."
#echo " ......................................................................... "

echo "VCXDK Make"
echo "=========="
echo


# Terminal Colors!
# echo -e "\e[1;31mHello World!"
COLOR_NC='\e[0m' # No Color
COLOR_BLACK='\e[0;30m'
COLOR_GRAY='\e[1;30m'
COLOR_RED='\e[0;31m'
COLOR_LIGHT_RED='\e[1;31m'
COLOR_GREEN='\e[0;32m'
COLOR_LIGHT_GREEN='\e[1;32m'
COLOR_BROWN='\e[0;33m'
COLOR_YELLOW='\e[1;33m'
COLOR_BLUE='\e[0;34m'
COLOR_LIGHT_BLUE='\e[1;34m'
COLOR_PURPLE='\e[0;35m'
COLOR_LIGHT_PURPLE='\e[1;35m'
COLOR_CYAN='\e[0;36m'
COLOR_LIGHT_CYAN='\e[1;36m'
COLOR_LIGHT_GRAY='\e[0;37m'
COLOR_WHITE='\e[1;37m'
case $TERM in
	xterm-*color)
		OK_MESSAGE="${COLOR_LIGHT_GREEN}OK${COLOR_NC}"
		ERROR_MESSAGE="${COLOR_LIGHT_RED}! ERROR !${COLOR_NC}"
		;;
	*)
		OK_MESSAGE="OK"
		ERROR_MESSAGE="! ERROR !"
		;;
esac

# Set INPUT_BASENAME if not already set
if [ -z ${INPUT_BASENAME+x} ]; then
	INPUT_BASENAME=$1
fi

INPUT_FILENAME=${INPUT_BASENAME}.c
S_FILENAME=${INPUT_BASENAME}.s
O_FILENAME=${INPUT_BASENAME}.o
OUTPUT_FILENAME=${INPUT_BASENAME}.bin



# Resolve paths
SOURCE_PATH=$(pwd)
TOOLS_PATH="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCLUDES_PATH=$(cd ${TOOLS_PATH}/../includes && pwd)
INCLUDES_PATH_RELATIVE=$(realpath --relative-to=${SOURCE_PATH} ${INCLUDES_PATH})

CR16TOOLSET_PATH=${TOOLS_PATH}/CR16toolset
CR16TOOLSET_PATH_RELATIVE=$(realpath --relative-to=${SOURCE_PATH} ${CR16TOOLSET_PATH})
CR16TOOLSET_PATH_WINE=${CR16TOOLSET_PATH_RELATIVE//\//\\}
CRCC_COMMAND="wine ${CR16TOOLSET_PATH}/crcc.exe"

CR16BASM_PATH=${TOOLS_PATH}/cr16b_asm
CR16BDASM_PATH=${TOOLS_PATH}/cr16b_dasm



# Default arguments
if [ -z ${ECHO_COMMANDS+x} ]; then
	ECHO_COMMANDS=1
fi

if [ -z ${CRT_FILENAME+x} ]; then
	CRT_FILENAME=${INCLUDES_PATH}/cart_header.asm
fi

if [ -z ${BINARY_SIZE+x} ]; then
	BINARY_SIZE=8192
fi

if [ -z ${CRCC_OPTIMIZE+x} ]; then
	CRCC_OPTIMIZE=
else
	CRCC_OPTIMIZE=-O
fi

if [ -z ${CR16BASM_VERBOSE+x} ]; then
	CR16BASM_ARG_VERBOSE=
	CR16BASM_ARG_STATS=
else
	CR16BASM_ARG_VERBOSE=--verbose
	CR16BASM_ARG_STATS=--stats
fi


echo "	Input file              : ${INPUT_FILENAME}"
echo "	Source path             : ${SOURCE_PATH}"
echo "	Tools path              : ${TOOLS_PATH}"
echo "	CR16 Toolset path       : ${CR16TOOLSET_PATH}"
echo "	CR16 Toolset path (WINE): ${CR16TOOLSET_PATH_WINE}"
echo "	cr16b_asm.py path       : ${CR16BASM_PATH}"
echo "	Includes path           : ${INCLUDES_PATH}"
echo "	Includes path (relative): ${INCLUDES_PATH_RELATIVE}"
echo "	CRT file                : ${CRT_FILENAME}"
echo "	Output file             : ${OUTPUT_FILENAME}"
echo "	Output size             : ${BINARY_SIZE}"

echo



# Stay in source path
cd ${SOURCE_PATH}

# Check
echo "### Checking..."
if [ ! -e ${INPUT_FILENAME} ]; then
	echo -e "${ERROR_MESSAGE}"
	echo "Input file \"${INPUT_FILENAME}\" does not exist! Stopping make."
	exit -1
fi
#echo -e ${OK_MESSAGE}
#echo



# Clean
echo "### Cleaning up..."
[ -e ${INPUT_BASENAME}.err ] && rm ${INPUT_BASENAME}.err
[ -e ${O_FILENAME} ] && rm ${O_FILENAME}
[ -e ${S_FILENAME} ] && rm ${S_FILENAME}
#echo -e ${OK_MESSAGE}
#echo



# Compile
echo "### Compiling \"${INPUT_FILENAME}\" to \"${S_FILENAME}\" using crcc..."

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
#export CRDIR=${CR16TOOLSET_PATH//\//\\}
export CRDIR=${CR16TOOLSET_PATH_WINE}

# Call the compiler using Wine
#wine ${CR16TOOLSET_PATH}/crcc.exe -mlarge -Wextra -I${INCLUDES_PATH} -c -S -n ${INPUT_FILENAME}
#wine ${CR16TOOLSET_PATH}/crcc.exe -mlarge -Wextra -O -I${INCLUDES_PATH_RELATIVE} -c -S -n ${INPUT_FILENAME}
CMD="${CRCC_COMMAND} -mlarge -Wextra ${CRCC_OPTIMIZE} -I${INCLUDES_PATH_RELATIVE} -c -S -n ${INPUT_FILENAME}"
if [ ${ECHO_COMMANDS} ]; then echo ${CMD}; fi
${CMD}

# Check result, stop if something went wrong
CRCC_RESULT=$?
if [ $CRCC_RESULT -ne 0 ]; then
	echo -e "${ERROR_MESSAGE}"
	echo "Compilation failed. Stopping make."
	exit $CRCC_RESULT
fi
if [ -e ${S_FILENAME} ]; then
	echo -e "${OK_MESSAGE}"
else
	echo -e "${ERROR_MESSAGE}"
	echo "Compiler did not produce assembly file \"${S_FILENAME}\". Stopping make."
	exit -10
fi

echo



#echo Disassembling using my own disasm...
#python3 ../cr16b_dasm/cr16b_dasm.py test.o


# Assemble binary
echo "### Assembling \"${OUTPUT_FILENAME}\" from \"${S_FILENAME}\"..."
# Turn the generated assembly into a binary file
#python3 ${CR16BASM_PATH}/cr16b_asm.py --verbose --output ${INPUT_BASENAME}.bin cart_header.asm ${INPUT_BASENAME}.s
#CMD="python3 ${CR16BASM_PATH}/cr16b_asm.py --stats ${CR16BASM_VERBOSE} --output ${OUTPUT_FILENAME} --pad ${BINARY_SIZE} ${CRT_FILENAME} ${INPUT_BASENAME}.s"
CMD="python3 ${CR16BASM_PATH}/cr16b_asm.py ${CR16BASM_ARG_STATS} ${CR16BASM_ARG_VERBOSE} --output ${OUTPUT_FILENAME} --pad ${BINARY_SIZE} ${CRT_FILENAME} ${INPUT_BASENAME}.s"
if [ ${ECHO_COMMANDS} ]; then echo ${CMD}; fi
${CMD}

# Check result, stop if something went wrong
CR16BASM_RESULT=$?
if [ $CR16BASM_RESULT -ne 0 ]; then
	echo -e "${ERROR_MESSAGE}"
	echo "Assembly failed. Stopping make."
	exit $CR16BASM_RESULT
fi
if [ -e ${OUTPUT_FILENAME} ]; then
	echo -e "${OK_MESSAGE}"
else
	echo "Assembler did not produce binary file \"${OUTPUT_FILENAME}\". Stopping make."
	exit -20
fi

echo



# Disassemble the result to check
#python3 ${CR16BDASM_PATH}/cr16b_dasm.py ${OUTPUT_FILENAME}


# Burn EEPROM
#echo "### Burning \"${OUTPUT_FILENAME}\"..."
#minipro -p 'AT28LV64@PLCC32' -w test.bin


echo "### Make finished."
