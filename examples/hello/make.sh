#!/bin/bash

INPUT_BASENAME=hello
#INPUT_BASENAME=hello_standalone

CR16TOOLSET_PATH=../../tools/CR16toolset
CR16BASM_PATH=../../tools/cr16b_asm
INCLUDES_PATH=../../includes
HEADER_FILENAME=${INCLUDES_PATH}/cart_header.asm
#HEADER_FILENAME=hello_standalone_header.asm
BINARY_SIZE=8192


# Clean
echo Cleaning up...
[ -e ${INPUT_BASENAME}.err ] && rm ${INPUT_BASENAME}.err
[ -e ${INPUT_BASENAME}.o ] && rm ${INPUT_BASENAME}.o
[ -e ${INPUT_BASENAME}.s ] && rm ${INPUT_BASENAME}.s


# Compile
echo Compiling \"${INPUT_BASENAME}.c\" using crcc...

# Wine passes exported environment variables over
# Create a backslash-version of the toolset path
export CRDIR=${CR16TOOLSET_PATH//\//\\}

# Call the compiler using Wine
wine ${CR16TOOLSET_PATH}/crcc.exe -mlarge -Wextra -I${INCLUDES_PATH} -c -S -n ${INPUT_BASENAME}.c

# Check result, stop if something went wrong
CRCC_RESULT=$?
if [ $CRCC_RESULT -ne 0 ]; then
	echo Compilation failed. Stopping make.
	exit $CRCC_RESULT
fi

#echo Disassembling using my own disasm...
#python3 ../cr16b_dasm/cr16b_dasm.py test.o


# Assemble binary
echo Assembling \"${INPUT_BASENAME}.bin\"...
# Turn the generated assembly into a binary file
#python3 ${CR16BASM_PATH}/cr16b_asm.py --verbose --output ${INPUT_BASENAME}.bin cart_header.asm ${INPUT_BASENAME}.s
python3 ${CR16BASM_PATH}/cr16b_asm.py --output ${INPUT_BASENAME}.bin --pad ${BINARY_SIZE} ${HEADER_FILENAME} ${INPUT_BASENAME}.s


# Disassemble the result to check
#python3 ../../tools/cr16b_dasm/cr16b_dasm.py test.bin


echo Finished.
