@ECHO OFF
SET CRDIR=Z:\apps\_code\CR16\Tools
SET PATH=%PATH%;%CRDIR%

ECHO Cleaning...
DEL *.err >NUL

REM SET INPUTNAME=%~dpn1
SET INPUTNAME=%~n1
ECHO INPUTNAME=%INPUTNAME%

ECHO Compiling...
REM	CompactRISC CR16 C Compiler Release 3.1 (revision 5)
REM	Usage: crcc [ [-flag] | [file] | [@argfile]  ] ... 
REM	              @argfile:  Read all, or part, of the flags from argfile
REM	                    -V:  Print compiler version
REM	           -o filename:  Specify an output file name
REM	                    -c:  Compile but do not link
REM	                    -g:  Generate symbolic debugging information
REM	                    -S:  Generate assembly code only
REM	                 -S -n:  Embed C source lines as comments in assembly file
REM	                    -O:  Optimize for speed
REM	                   -Os:  Optimize for space
REM	                   -ON:  Optimize for speed and perform loop unrolling
REM	                   -Oi:  Optimize and treat all globals as volatile
REM	                -sbrel:  Use static base register optimization
REM	               -J[1|2]:  Set largest alignment within structures
REM	              -KB[1|2]:  Set bus width (alignment of stack)
REM	         -fshort-enums:  Select the shortest size for enumeration type
REM	    -finline-functions:  Integrate all simple functions into their callers
REM	-fkeep-inline-functions: Keep body of inline functions
REM	       -ffixed-r[7-13]:  Do not use register r<n> (e.g. -ffixed-r10)
REM	               -mcr16c:  Generate code for CR16C standard mode (default)
REM	             -mcr16csr:  Generate code for CR16C compatible mode
REM	           -mcr16cplus:  Generate code for CR16CPlus
REM	               -msmall:  Generate code for CR16B small memory model
REM	               -mlarge:  Generate code for CR16B large memory model
REM	             -mall-far:  Treat all variables as far
REM	                -mfar2:  Allocate far variables in the whole memory space
REM	                         (CR16B and CR16CPlus only)
REM	                 -ansi:  Accept only strict ANSI C programs
REM	               -Wextra:  Warn about non-obvious potential problems
REM	         -Wno-<option>:  Disable warning <option>
REM	                    -w:  No warning diagnostics
REM	                    -Q:  Error checking only
REM	                    -v:  Verbose mode (show compilation stages)
REM	                   -vn:  Verbose mode without actually executing
REM	                    -z:  Dump errors and warnings into <file>.err
REM	         -zn<filename>:  Dump errors and warnings into <filename>
REM	Preprocessor flags: 
REM	                    -E:  Run cpp only, redirect output to stdout
REM	                    -P:  Run cpp only, redirect output to <file>.i
REM	        -Dsymbol[=def]:  Define cpp symbol
REM	              -Usymbol:  Undefine cpp symbol
REM	                 -Idir:  Specify additional directory for included files
REM	                    -M:  Generate makefile dependencies
REM	
REM	Linking flags:
REM	                -lname:  Specify a standard library for the linker
REM	          -KFemulation:  Use floating point emulation library
REM	                 -Ldir:  Specify the libraries directory
REM	    -W[p|c|a|l],option:  Pass option to different stages
REM	                   -Wp:     preprocessor
REM	                   -Wc:     compiler
REM	                   -Wa:     assembler
REM	                   -Wl:     linker

REM cc.arg:
REM	-DNATIONAL_COMPILER
REM	-DFSYS=20000000UL
REM	-DBAUD_RATE=115200UL
REM	-DUART_FRAME=N81
REM	-DSW_FLOW_CTRL
REM	-DnoHW_FLOW_CTRL
REM	-Oi
REM	-Os
REM	-g
REM	-z
REM	-n
REM	-S
REM	-J1

REM crcc @cc.arg -v -mlarge -Dfoo=bar test.c
REM crcc @cc.arg -msmall -Wextra -S test.c
REM crcc @cc.arg -mlarge -Wextra -S test.c
REM crcc @cc.arg -mlarge -Wextra %INPUTNAME%.c
REM crcc -mlarge -Wextra %INPUTNAME%.c
crcc -mlarge -Wextra -S -n %INPUTNAME%.c


ECHO Assembling...
REM	CompactRISC Assembler Release 3.1 (revision 2)
REM	Usage: crasm [flag] ... filename
REM	      -ds|-dm|-dl : set the default displacement size
REM	               -c : runs the C compiler pre-processor (cpp)
REM	               -r : incorporates the data segment into the text segment
REM	               -s : save compiler-generated labels in object file symbol table
REM	               -V : write the version number of the assembler to stderr
REM	               -v : use virtual memory for intermediate storage
REM	     -L[filename] : produce listing to filename | stdout
REM	               -n : disable displacement size optimization
REM	               -o : output object file name
REM	               -t : show all utilities called by the assembler
REM	      @{filename} : reads options from file filename (MS-DOS only)
REM	               -w : suppress assembler warning messages
REM	     -y[filename] : produce a symbol table in filename | stdout
REM	     -x[filename] : produce a cross-reference file in filename |stdout
REM	-D{name|name=def} : define a name to cpp
REM	         -U{name} : remove previous definition of predefined name
REM	          -I{dir} : first search for include files in directory dir
REM	               -g : produce additional line number information for debbuging
REM	       -M[option] : invoke macro assembler [with option]
REM	 -z -zn[filename] : also output messages to file
REM	          -msmall : CR16B small memory model 
REM	          -mlarge : CR16B large memory model 
REM	        -mcr16csr : CR16CSR model 
REM	          -mcr16c : CR16C model (default)
REM	      -mcr16cplus : CR16CPLUS model 

REM crasm -z -Ltest.lis test.s
REM crasm -x -y -v -z -t -mlarge test.s
REM crasm -z -t -mlarge -ytest.sym -xtest.x -Ltest.lis -r test.s
REM crasm -z -t -mlarge -ytest.sym -xtest.x -Ltest.lis -r test.s
crasm -z -t -mlarge -r %INPUTNAME%.s


ECHO Disassembling...
REM	CompactRISC Object View Utility Release 3.1 (revision 2)
REM	Usage: crview [-hnrlVaTDIOe] [-f[ctnabezksh]] [[-s[[n|v]ug]]|[-S[[n|v]ugx]]]
REM		      [-z[nx]] file ...
REM		 -h : display file headers
REM		 -n : display section headers
REM		 -r : display relocation info
REM		 -l : display line number info
REM		 -V : display the Release and Revsion
REM		 -a : display archive symbol directory
REM		 -T : disassemble .text section(s)
REM		 -D : dump .data section(s)
REM		 -I : dump .init section(s)
REM		 -O : dump all sections
REM		 -e : ignore disassembler errors
REM		 -f[ctnabezksh] : display function information, Options are:
REM		   c-Class,  display the Class of the function (e.g extern)
REM		   t-Type, display the Type of the function (e.g int)
REM		   n-Name, display the Name of the function
REM		   a-Arguments, display the Arguments that the function gets
REM		   b-Begin address, display the address in which the function Begins
REM		   e-End-address, display the address in which the function Ends
REM		   z-Size, display the Size of the function
REM		   k-Stack, display the place that the function needs on the Stack
REM		   s-Source file, dispaly the Source file and the line number in which
REM		   the function appeares
REM		   h-Header, display the Header of the function information table
REM		 -s[[n|v]ug] : display symbol table in long format, Options are:
REM		   n-Name sort, v-Value sort, u-User symbols, g-Global and static.
REM		 -S[[n|v]ugxf] : display symbol table in short format, Options are:
REM		   n-Name sort, v-Value sort, u-User symbols, g-Global and static,
REM		   x-Hexadecimal,f-Full names.
REM		 -z[nx] : display sections size, Options are:
REM		   n-Include noload, x-Hexadecimal.
REM		 Default: all above options except for '-f', '-z' and '-S'.

crview -T -O %INPUTNAME%.o

REM ECHO Extracting bin?
REM crlink -o %INPUTNAME%.out %INPUTNAME%.o

ECHO End of make.bat
