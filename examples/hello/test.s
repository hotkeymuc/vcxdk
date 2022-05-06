#	National Semiconductor Corporation
#	CompactRISC CR16 C Compiler Version 3.1 (revision 5)
#	-- test.s --	Fri May 06 11:58:30 2022
#
# cc1 compilation options:
#
#  -fomit-frame-pointer -fforce-mem -fforce-addr -ffunction-cse
# -fkeep-static-consts -fpcc-struct-return -fsjlj-exceptions -fcommon
# -fgnu-linker -fargument-alias -fident -Wunused -Wshadow -Wswitch -mregparm
# -mshort -mannotate -mregrel -msections -mscond -mcr16 -mlarge
# -mbiggest-alignment-16 -mbiggest-struct-alignment-16

gcc2_compiled.:
	.file	"test.c"
#--- 
#--- 
#--- 
#--- 
#--- 
#--- void alert(__far char *text) {
	.text
	.align	2
	.globl	_alert
_alert:
	addw	$-4,sp
	storw	r2,0(sp)
	storw	r3,2(sp)
#--- (void)text; 
#--- 
#--- __asm__("push $2, era");
	push    $2, era
#--- 
#--- 
#--- __asm__("movd $0x034191, (r1,r0)"); 
	movd    $0x034191, (r1,r0)
#--- __asm__("adduw $-0x8, sp");
	adduw   $-0x8, sp
#--- __asm__("storw r0, 0x4(sp)");
	storw   r0, 0x4(sp)
#--- __asm__("storw r1, 0x6(sp)");
	storw   r1, 0x6(sp)
#--- 
#--- 
#--- 
#--- __asm__("movw r3, r1");
	movw    r3, r1
#--- __asm__("movw r2, r0");
	movw    r2, r0
#--- __asm__("adduw $0x10, r1"); 
	adduw   $0x10, r1
#--- 
#--- __asm__("storw r0, 0(sp)");
	storw   r0, 0(sp)
#--- __asm__("storw r1, 0x2(sp)");
	storw   r1, 0x2(sp)
#--- 
#--- __asm__("movb $0, r4"); 
	movb    $0, r4
#--- __asm__("movd $0x084D40, (r3,r2)"); 
	movd    $0x084D40, (r3,r2)
#--- __asm__("bal (ra,era), 0x198CC4"); 
	bal     (ra,era), 0x198CC4
#--- 
#--- __asm__("adduw $0x8, sp");
	adduw   $0x8, sp
#--- 
#--- 
#--- __asm__("pop $2, era");
	pop     $2, era
#--- 
#--- }
.L2:
	subw	$-4,sp
	jump	(ra,era)
#--- int prompt(__far char *title, __far char *text) {
	.align	2
	.globl	_prompt
_prompt:
	addw	$-8,sp
	storw	r2,0(sp)
	storw	r3,2(sp)
	storw	r4,4(sp)
	storw	r5,6(sp)
#--- (void)title;
#--- (void)text;
#--- 
#--- __asm__("push $2, era");
	push    $2, era
#--- 
#--- 
#--- __asm__("movd $0x034191, (r1,r0)"); 
	movd    $0x034191, (r1,r0)
#--- __asm__("push $2, r0");
	push    $2, r0
#--- 
#--- 
#--- __asm__("adduw $0x10, r3"); 
	adduw   $0x10, r3
#--- 
#--- __asm__("adduw $0x10, r5"); 
	adduw   $0x10, r5
#--- 
#--- __asm__("bal (ra,era), 0x1805C4"); 
	bal     (ra,era), 0x1805C4
#--- __asm__("adduw $0x4, sp");
	adduw   $0x4, sp
#--- 
#--- 
#--- 
#--- 
#--- 
#--- 
#--- 
#--- __asm__("pop $2, era");
	pop     $2, era
#--- 
#--- 
#--- 
#--- }
.L3:
	subw	$-8,sp
	jump	(ra,era)
#--- 
#--- __far const char hello[] = "Hello there";
	.globl	_hello
	.section	.frdat_2,"r"
	.align	2
_hello:
	.ascii "Hello there\0"
#--- __far const char world[] = "World!!";
	.globl	_world
	.align	2
_world:
	.ascii "World!!\0"
#--- __far const char yes[] = "YES!!";
	.globl	_yes
	.align	2
_yes:
	.ascii "YES!!\0"
#--- __far const char no[] = "NO!";
	.globl	_no
	.align	2
_no:
	.ascii "NO!\0"
#--- void main(void) {
	.code_label	_alert
	.code_label	_prompt
	.code_label	_alert
	.code_label	_alert
	.text
	.align	2
	.globl	_main
_main:
	push	$2,era
#--- 
#--- 
#--- 
#--- alert(&hello);
	movd	$_hello,(r3,r2)
	bal	(ra,era),_alert
#--- 
#--- while(1) {
.L5:
.L7:
#--- if (prompt(&hello, &world) == 1)
	movd	$_hello,(r3,r2)
	movd	$_world,(r5,r4)
	bal	(ra,era),_prompt
	cmpw	$1,r0
	bne	.L8
#--- alert(&yes);
	movd	$_yes,(r3,r2)
	bal	(ra,era),_alert
#--- else
#--- alert(&no);
	br	.L9
.L8:
	movd	$_no,(r3,r2)
	bal	(ra,era),_alert
.L9:
#--- }
	br	.L5
#--- 
#--- }
	popret	$2,era
