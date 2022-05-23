#!/usr/bin/python3
"""
Tests for the
Not-yet-Assembler for
National Semiconductor's CR16B CPU

2022-04-23 Bernhard "HotKey" Slawik
"""

from cr16b_asm import CR16B_Assembler

def put(t):
	print(t)
def put_debug(t):
	#pass
	print(t)

### Tests
def assert_assembly(text, bin, pc=0x0000):
	"""Helper function to check assembly text against asserted binary output"""
	
	
	put_debug('Checking "%06X	%s" =?= %s' % (pc, text, ' '.join([ '%02X' % b for b in bin]) ))
	
	
	asm = CR16B_Assembler()
	#bin2 = asm.assemble(text, pc=pc)
	asm._assemble(text, pc=pc, echo_lines=False)	# Only single pass needed
	
	# Compare the text section
	bin2 = asm.sections['text'].store.get_bytes()
	
	assert len(bin) == len(bin2), 'Assembled binary sizes differs!\nAsserted: %s\nProduced: %s' % (' '.join([ '%02X' % b for b in bin]), ' '.join([ '%02X' % b for b in bin2]))
	
	for i in range(len(bin)):
		assert bin2[i] == bin[i], 'Binary difference at [%d]: 0x%02X != 0x%02X\nAsserted: %s\nProduced: %s' % (i, bin2[i], bin[i], ' '.join([ '%02X' % b for b in bin]), ' '.join([ '%02X' % b for b in bin2]))
	
	#put('Okay!')
	return True

def test_instructions():
	"""Compare assembled code against known binary output"""
	
	#asm = CR16B_Assembler()
	
	# Test: 0001A6:	00 02      	0200     	nop
	assert_assembly('nop', [0x00, 0x02])
	
	# Test: 0001C4:	DE 7D      	7DDE     	di
	assert_assembly('di', [0xde, 0x7d])
	# Test: 0001D0:	FE 7D      	7DFE     	ei
	assert_assembly('ei', [0xfe, 0x7d])
	# Test: 00020C:	FE 7F      	7FFE     	wait
	assert_assembly('wait', [0xfe, 0x7f])
	
	
	# Test: 02A6EC:	06 26      	2606     	mulw    $0x6, r0
	assert_assembly('mulw    $0x6, r0', [0x06, 0x26])
	# Test: 0026B6:	2A 26      	262A     	mulw    $0xA, r1
	assert_assembly('mulw    $0xA, r1', [0x2a, 0x26])
	# Test: 0154D4:	65 26      	2665     	mulw    $0x5, r3
	assert_assembly('mulw    $0x5, r3', [0x65, 0x26])
	# Test: 000A22:	B0 26      	26B0     	mulw    $-0x10, r5
	assert_assembly('mulw    $-0x10, r5', [0xb0, 0x26])
	# Test: 0012A2:	61 66      	6661     	mulw    r0, r3
	assert_assembly('mulw    r0, r3', [0x61, 0x66])
	
	#@FIXME: Support this special case:
	#	# Test: 00279E:	04 63      	6304     	mulsw   r2, (r9,r8)
	#	assert_assembly('mulsw   r2, (r9,r8)', [0x04, 0x63])
	#	
	#	# Test: 0041E4:	02 7E      	7E02     	muluw   r1, (r1,r0)
	#	assert_assembly('muluw   r1, (r1,r0)', [0x02, 0x7e])
	
	# Test: 000A54:	99 29      	2999     	ashuw   $-7, r12
	assert_assembly('ashuw   $-7, r12', [0x99, 0x29])
	# Test: 0328AE:	05 68      	6805     	ashuw   r2, r0
	assert_assembly('ashuw   r2, r0', [0x05, 0x68])
	# Test: 01C770:	18 28      	2818     	ashuw   $-8, r0
	assert_assembly('ashuw   $-8, r0', [0x18, 0x28])
	# Test: 0017C0:	91 28 F1 FF	2891 FFF1	ashuw   $65521, r4
	assert_assembly('ashuw   $65521, r4', [0x91, 0x28, 0xf1, 0xff])
	
	
	#@TODO: Implement! Including relative addresses!
	# Load and Store
	
	# Test: 034168:	C2 04 0C 79	04C2 790C	storb   $0x1, 0x0790C
	assert_assembly('storb   $0x1, 0x0790C', [0xc2, 0x04, 0x0c, 0x79])
	# Test: 033CB0:	3F F9 10 79	F93F 7910	storw   r9, 0x07910
	assert_assembly('storw   r9, 0x07910', [0x3f, 0xf9, 0x10, 0x79])
	# Test: 033E3E:	9E E8      	E89E     	storw   r4, 0x8(sp)
	assert_assembly('storw   r4, 0x8(sp)', [0x9e, 0xe8])
	# Test: 033E40:	BE EA      	EABE     	storw   r5, 0xA(sp)
	assert_assembly('storw   r5, 0xA(sp)', [0xbe, 0xea])
	
	# Test: 002552:	1F F0 9C 00	F01F 009C	storw   r0, 0x9C(sp)
	assert_assembly('storw   r0, 0x9C(sp)', [0x1f, 0xf0, 0x9c, 0x00])
	# Test: 002556:	3F F0 9E 00	F03F 009E	storw   r1, 0x9E(sp)
	assert_assembly('storw   r1, 0x9E(sp)', [0x3f, 0xf0, 0x9e, 0x00])
	
	# Test: 001020:	E5 F8 10 00	F8E5 0010	storw   r7, 0x10(r3,r2)
	assert_assembly('storw   r7, 0x10(r3,r2)', [0xe5, 0xf8, 0x10, 0x00])
	# Test: 001008:	A5 F9 04 00	F9A5 0004	storw   era, 0x4(r3,r2)
	assert_assembly('storw   era, 0x4(r3,r2)', [0xa5, 0xf9, 0x04, 0x00])
	
	# Test: 03D3AC:	C1 24 02 00	24C1 0002	storw   $0, 0x2(r0)
	assert_assembly('storw   $0, 0x2(r0)', [0xc1, 0x24, 0x02, 0x00])
	# Test: 03CE4C:	C1 64      	64C1     	storw   $0, 0(r0)
	assert_assembly('storw   $0, 0(r0)', [0xc1, 0x64])
	# Test: 03CE3E:	03 D0 43 7B	D003 7B43	storb   r0, 0x7B43(r1)
	assert_assembly('storb   r0, 0x7B43(r1)', [0x03, 0xd0, 0x43, 0x7b])
	
	# Test: 003154:	1F B0 22 00	B01F 0022	loadw   0x22(sp), r0
	assert_assembly('loadw   0x22(sp), r0', [0x1f, 0xb0, 0x22, 0x00])
	# Test: 003158:	3F B0 24 00	B03F 0024	loadw   0x24(sp), r1
	assert_assembly('loadw   0x24(sp), r1', [0x3f, 0xb0, 0x24, 0x00])
	# Test: 00316E:	9F B0 32 00	B09F 0032	loadw   0x32(sp), r4
	assert_assembly('loadw   0x32(sp), r4', [0x9f, 0xb0, 0x32, 0x00])
	# Test: 003172:	BF B0 34 00	B0BF 0034	loadw   0x34(sp), r5
	assert_assembly('loadw   0x34(sp), r5', [0xbf, 0xb0, 0x34, 0x00])
	# Test: 002548:	1F B0 9C 00	B01F 009C	loadw   0x9C(sp), r0
	assert_assembly('loadw   0x9C(sp), r0', [0x1f, 0xb0, 0x9c, 0x00])
	# Test: 00254C:	3F B0 9E 00	B03F 009E	loadw   0x9E(sp), r1
	assert_assembly('loadw   0x9E(sp), r1', [0x3f, 0xb0, 0x9e, 0x00])
	# Test: 0025A0:	1F B0 A0 00	B01F 00A0	loadw   0xA0(sp), r0
	assert_assembly('loadw   0xA0(sp), r0', [0x1f, 0xb0, 0xa0, 0x00])
	# Test: 0025A4:	3F B0 A2 00	B03F 00A2	loadw   0xA2(sp), r1
	assert_assembly('loadw   0xA2(sp), r1', [0x3f, 0xb0, 0xa2, 0x00])
	# Test: 037F62:	C9 BF 05 0D	BFC9 0D05	loadw   -0xF2FB(r5,r4), ra
	assert_assembly('loadw   -0xF2FB(r5,r4), ra', [0xc9, 0xbf, 0x05, 0x0d])
	# Test: 037F6E:	C3 BF 05 38	BFC3 3805	loadw   -0xC7FB(r2,r1), ra
	assert_assembly('loadw   -0xC7FB(r2,r1), ra', [0xc3, 0xbf, 0x05, 0x38])
	
	# Test: 033F96:	5F 98 32 79	985F 7932	loadb   0x07932, r2
	assert_assembly('loadb   0x07932, r2', [0x5f, 0x98, 0x32, 0x79])
	# Test: 033C74:	1F B8 10 79	B81F 7910	loadw   0x07910, r0
	assert_assembly('loadw   0x07910, r0', [0x1f, 0xb8, 0x10, 0x79])
	# Test: 033EB8:	05 98 00 00	9805 0000	loadb   0(r3,r2), r0
	assert_assembly('loadb   0(r3,r2), r0', [0x05, 0x98, 0x00, 0x00])
	# Test: 033E4A:	5E A8      	A85E     	loadw   0x8(sp), r2
	assert_assembly('loadw   0x8(sp), r2', [0x5e, 0xa8])
	# Test: 033E4C:	7E AA      	AA7E     	loadw   0xA(sp), r3
	assert_assembly('loadw   0xA(sp), r3', [0x7e, 0xaa])
	
	
	
	# Test MOVx
	# Test: 034434:	06 18      	1806     	movb    $0x06, r0
	assert_assembly('movb    $0x06, r0', [0x06, 0x18])
	
	
	# Edge cases with weird different sizes:
	
	# Test: 0001D8:	11 18 C0 FF	1811 FFC0	movb    $0xC0, r0
	assert_assembly('movb    $0xC0, r0', [0x11, 0x18, 0xc0, 0xff])
	# Test: 0001E8:	10 18      	1810     	movb    $0xF0, r0
	assert_assembly('movb    $0xF0, r0', [0x10, 0x18])
	# Test: 000202:	1F 18      	181F     	movb    $0xFF, r0
	assert_assembly('movb    $0xFF, r0', [0x1f, 0x18])
	
	# Test: 034420:	0F 78      	780F     	movw    r7, r0
	assert_assembly('movw    r7, r0', [0x0f, 0x78])
	# Test: 000004:	11 38 00 01	3811 0100	movw    $0x0100, r0
	assert_assembly('movw    $0x0100, r0', [0x11, 0x38, 0x00, 0x01])
	# Test: 00013E:	91 39 00 00	3991 0000	movw    $0x0000, r12
	assert_assembly('movw    $0x0000, r12', [0x91, 0x39, 0x00, 0x00])
	
	
	# Test: 034442:	02 6A      	6A02     	movzb   r1, r0
	assert_assembly('movzb   r1, r0', [0x02, 0x6a])
	# Test: 0360CA:	C0 6A      	6AC0     	movzb   r0, r6
	assert_assembly('movzb   r0, r6', [0xc0, 0x6a])
	
	# Test: 0027B2:	04 69      	6904     	movxb   r2, r8
	assert_assembly('movxb   r2, r8', [0x04, 0x69])
	# Test: 002DD0:	00 68      	6800     	movxb   r0, r0
	assert_assembly('movxb   r0, r0', [0x00, 0x68])
	
	# Test MOVD
	# Test: 000682:	00 66 98 09	6600 0998	movd    $0x100998, (r1,r0)
	#asm.assemble_movd(imm21=0x100998, dest_pair=0b0000)
	assert_assembly('movd    $0x100998, (r1,r0)', [0x00, 0x66, 0x98, 0x09])
	# Test: 0004AC:	20 66 FA 09	6620 09FA	movd    $0x1009FA, (r2,r1)
	#asm.assemble_movd(imm21=0x1009FA, dest_pair=0b0001)
	assert_assembly('movd    $0x1009FA, (r2,r1)', [0x20, 0x66, 0xfa, 0x09])
	# Test: 0004C6:	4C 66 00 00	664C 0000	movd    $0x1C0000, (r3,r2)
	#asm.assemble_movd(imm21=0x1C0000, dest_pair=0b0010)
	assert_assembly('movd    $0x1C0000, (r3,r2)', [0x4c, 0x66, 0x00, 0x00])
	# Test: 000588:	80 66 0C 0B	6680 0B0C	movd    $0x100B0C, (r5,r4)
	#asm.assemble_movd(imm21=0x100B0C, dest_pair=0b0100)
	assert_assembly('movd    $0x100B0C, (r5,r4)', [0x80, 0x66, 0x0c, 0x0b])
	
	
	# Test PUSH/POP/POPRET
	# Test: 025674:	3A 6C      	6C3A     	push    $2, era
	assert_assembly('push    $2, era', [0x3a, 0x6c])
	# Test: 025676:	6E 6C      	6C6E     	push    $4, r7
	assert_assembly('push    $4, r7', [0x6e, 0x6c])
	
	# Test: 000458:	EE 6C      	6CEE     	pop     $4, r7
	#asm.assemble_pop(reg=REG_R7, count=4)	# pop     $4, r7
	assert_assembly('pop     $4, r7', [0xee, 0x6c])
	# Test: 000928:	96 6C      	6C96     	pop     $1, r11
	#asm.assemble_pop(reg=REG_R11, count=1)	# pop     $1, r11
	assert_assembly('pop     $1, r11', [0x96, 0x6c])
	
	# Test: 00041A:	BA 6D      	6DBA     	popret  $2, era ; LMM
	#asm.assemble_popret(reg=REG_ERA, count=2)	# popret  $2, era ; LMM
	assert_assembly('popret  $2, era ; LMM', [0xba, 0x6d])
	
	
	# Test add/sub with different format qualifiers
	# Test: 0020FA:	00 00      	0000     	addb    $0, r0
	assert_assembly('addb    $0, r0', [0x00, 0x00])
	
	# Test: 001270:	D1 00 11 00	00D1 0011	addb    $0x11, r6
	assert_assembly('addb    $0x11, r6', [0xd1, 0x00, 0x11, 0x00])
	
	# Test: 03301C:	60 13      	1360     	addcb   $0, r11
	assert_assembly('addcb   $0, r11', [0x60, 0x13])
	# Test: 03443C:	01 02      	0201     	addub   $0x1, r0
	assert_assembly('addub   $0x1, r0', [0x01, 0x02])
	# Test: 001094:	89 60      	6089     	addw    r4, r4
	assert_assembly('addw    r4, r4', [0x89, 0x60])
	# Test: 001900:	11 20 00 08	2011 0800	addw    $0x800, r0
	assert_assembly('addw    $0x800, r0', [0x11, 0x20, 0x00, 0x08])
	# Test: 001F14:	31 22 00 10	2231 1000	adduw   $0x1000, r1
	assert_assembly('adduw   $0x1000, r1', [0x31, 0x22, 0x00, 0x10])
	# Test: 001F18:	40 32      	3240     	addcw   $0, r2
	assert_assembly('addcw   $0, r2', [0x40, 0x32])
	# Test: 001092:	01 72      	7201     	addcw   r0, r0
	assert_assembly('addcw   r0, r0', [0x01, 0x72])
	
	# Test: 000460:	F1 23 E6 FF	23F1 FFE6	adduw   $-0x1A, sp
	assert_assembly('adduw   $-0x1A, sp', [0xf1, 0x23, 0xe6, 0xff])
	# Test: 01DF14:	F8 23      	23F8     	adduw   $-0x8, sp
	assert_assembly('adduw   $-0x8, sp', [0xf8, 0x23])
	
	# Test: 001288:	D1 1E 10 00	1ED1 0010	subb    $0x10, r6
	assert_assembly('subb    $0x10, r6', [0xd1, 0x1E, 0x10, 0x00])
	# Test: 002A2A:	02 1E      	1E02     	subb    $0x2, r0
	assert_assembly('subb    $0x2, r0', [0x02, 0x1E])
	# Test: 00204A:	A1 3E      	3EA1     	subw    $0x1, r5
	assert_assembly('subw    $0x1, r5', [0xA1, 0x3E])
	# Test: 00204C:	C0 3A      	3AC0     	subcw   $0, r6
	assert_assembly('subcw   $0, r6', [0xc0, 0x3a])
	
	# Test: 00149E:	91 30 00 80	3091 8000	andw    $0x8000, r4
	assert_assembly('andw    $0x8000, r4', [0x91, 0x30, 0x00, 0x80])
	# Test: 0014AA:	71 30 7F 00	3071 007F	andw    $0x007F, r3
	assert_assembly('andw    $0x007F, r3', [0x71, 0x30, 0x7f, 0x00])
	# Test: 0018A4:	51 31 FF 07	3151 07FF	andw    $0x07FF, r10
	assert_assembly('andw    $0x07FF, r10', [0x51, 0x31, 0xff, 0x07])
	# Test: 0018A8:	EF 30      	30EF     	andw    $0x000F, r7
	assert_assembly('andw    $0x000F, r7', [0xef, 0x30])
	
	# Test: 0018AE:	F1 1C 10 00	1CF1 0010	orb     $0x10, r7
	assert_assembly('orb     $0x10, r7', [0xf1, 0x1c, 0x10, 0x00])
	# Test: 0014CC:	31 1C 80 FF	1C31 FF80	orb     $0x80, r1
	assert_assembly('orb     $0x80, r1', [0x31, 0x1c, 0x80, 0xff])
	# Test: 0018B8:	13 7D      	7D13     	orw     r9, r8
	assert_assembly('orw     r9, r8', [0x13, 0x7d])
	# Test: 001A68:	01 3D      	3D01     	orw     $0x0001, r8
	assert_assembly('orw     $0x0001, r8', [0x01, 0x3d])
	
	# Test: 0010E4:	0B 6C      	6C0B     	xorw    r5, r0
	assert_assembly('xorw    r5, r0', [0x0b, 0x6c])
	
	# Test: 001084:	28 2A      	2A28     	lshw    $8, r1
	assert_assembly('lshw    $8, r1', [0x28, 0x2a])
	# Test: 00116E:	BF 2A      	2ABF     	lshw    $-1, r5
	assert_assembly('lshw    $-1, r5', [0xbf, 0x2a])
	# Test: 0011E4:	DF 2A      	2ADF     	lshw    $-1, r6
	assert_assembly('lshw    $-1, r6', [0xdf, 0x2a])
	# Test: 0010E2:	17 2A      	2A17     	lshw    $-9, r0
	assert_assembly('lshw    $-9, r0', [0x17, 0x2a])
	# Test: 001A90:	75 6B      	6B75     	lshw    r10, r11
	assert_assembly('lshw    r10, r11', [0x75, 0x6b])
	
	
	
	# Test BAL
	# 00006E:	B2 77 90 35	77B2 3590	bal     (ra,era), 0x0335FE
	#asm.assemble_bal(pc = 0x00006E, dest = 0x0335FE)
	assert_assembly('bal     (ra,era), 0x0335FE', [0xb2, 0x77, 0x90, 0x35], pc=0x00006e)
	# 0021EC:	A0 77 34 03	77A0 0334	bal     (ra,era), 0x002520
	#asm.assemble_bal(pc = 0x0021EC, dest = 0x002520)
	assert_assembly('bal     (ra,era), 0x002520', [0xa0, 0x77, 0x34, 0x03], pc=0x0021EC)
	# 0034BA:	BE 77 CB E4	77BE E4CB	bal     (ra,era), 0x001984
	#asm.assemble_bal(pc = 0x00006E, dest = 0x0335FE)
	assert_assembly('bal     (ra,era), 0x001984', [0xBE, 0x77, 0xCB, 0xE4], pc=0x0034BA)
	# 033CAC:	A0 77 26 04	77A0 0426	bal     (ra,era), 0x0340D2
	#asm.assemble_bal(pc = 0x00006E, dest = 0x0335FE)
	assert_assembly('bal     (ra,era), 0x0340D2', [0xa0, 0x77, 0x26, 0x04], pc=0x033CAC)
	# Test: Update Cart: 0006FA:	B6 77 9F FD	77B6 FD9F	bal     (ra,era), 0x180498
	assert_assembly('bal     (ra,era), 0x180498', [0xb6, 0x77, 0x9f, 0xfd], pc=0x0006FA)
	#asm.assemble_bal(pc=0x0006FA, dest=0x180498)
	#asm.assemble_bal(pc=0x00020E, dest=0x1805c4)
	#asm.assemble_bal(pc=0x000222, dest=0x1805c4)
	#asm.assemble_bal(pc=0x000538, dest=0x018D18)
	
	# Test: 000A48:	66 16      	1666     	jal     (r4,r3), (r4,r3)
	assert_assembly('jal     (r4,r3), (r4,r3)', [0x66, 0x16], pc=0x000A48)
	# Test: 0025A8:	A0 17      	17A0     	jal     (ra,era), (r1,r0)
	assert_assembly('jal     (ra,era), (r1,r0)', [0xa0, 0x17], pc=0x0025A8)
	# Test: 0151C8:	A4 17      	17A4     	jal     (ra,era), (r3,r2)
	assert_assembly('jal     (ra,era), (r3,r2)', [0xa4, 0x17], pc=0x0151C8)
	
	
	# Test: JUMP
	# Test: 001026:	DB 17      	17DB     	jump    (ra,era)
	#asm.assemble_jump(reg_pair=REG_ERA)	# jump    (ra,era)
	assert_assembly('jump    (ra,era)', [0xdb, 0x17], pc=0x001026)
	
	# Test: Simple branch
	# Test: 000304:	C2 75 CC F6	75C2 F6CC	br      0x02F9D0
	#asm.assemble_br(disp=(0x02F9D0 - 0x000304))	#, cond=0x0e)
	assert_assembly('br      0x02F9D0', [0xc2, 0x75, 0xcc, 0xf6], pc=0x000304)
	# Test: 03385C:	DE 75 07 FF	75DE FF07	br      0x033762
	#asm.assemble_br(disp=(0x033762 - 0x03385C))
	assert_assembly('br      0x033762', [0xde, 0x75, 0x07, 0xff], pc=0x03385C)
	
	# Test: Compare-and-Branch
	#@FIXME: This does not work!
	## Test: 015946:	1D 14      	141D     	beq0b   r0, 0x01594A
	##asm.assemble_beq(op=0xe, opext=3, i=I_BYTE, reg=REG_R0, imm4m1=(0x01594A - 0x015946))
	# Test: 03194A:	09 15      	1509     	beq0b   r8, 0x031952
	#asm.assemble_brcondi(cond=COND_EQ, val1=0, i=I_BYTE, reg=REG_R8, disp5m1=(0x031952 - 0x03194A))
	assert_assembly('beq0b   r8, 0x031952', [0x09, 0x15], pc=0x03194A)
	# Test: 031964:	49 15      	1549     	beq1b   r8, 0x03196C
	#asm.assemble_brcondi(cond=COND_EQ, val1=1, i=I_BYTE, reg=REG_R8, disp5m1=(0x03196C - 0x031964))
	assert_assembly('beq1b   r8, 0x03196C', [0x49, 0x15], pc=0x031964)
	# Test: 015412:	8D 14      	148D     	bne0b   r0, 0x01541E	; back to loop
	#asm.assemble_brcondi(cond=COND_NE, val1=0, i=I_BYTE, reg=REG_R0, disp5m1=(0x1541E - 0x015412))
	assert_assembly('bne0b   r0, 0x01541E	; back!', [0x8d, 0x14], pc=0x015412)
	# Test: 015904:	CB 14      	14CB     	bne1b   r0, 0x01590E
	#asm.assemble_brcondi(cond=COND_NE, val1=1, i=I_BYTE, reg=REG_R0, disp5m1=(0x01590E - 0x015904))
	assert_assembly('bne1b   r0, 0x01590E', [0xcb, 0x14], pc=0x015904)
	#Test: 002256:	89 34      	3489     	bne0w   r0, 0x00225E
	assert_assembly('bne0w   r0, 0x00225E', [0x89, 0x34], pc=0x002256)
	
	# Test: 0014E6:	11 0E 80 FF	0E11 FF80	cmpb    $-0x80, r0
	assert_assembly('cmpb    $-0x80, r0', [0x11, 0x0e, 0x80, 0xff])
	# Test: 0014D2:	20 2E      	2E20     	cmpw    $0, r1
	assert_assembly('cmpw    $0, r1', [0x20, 0x2e], pc=0x0014D2)
	# Test: 0014D4:	D2 40      	40D2     	bgt     0x0014E6
	assert_assembly('bgt     0x0014E6', [0xd2, 0x40], pc=0x0014D4)
	# Test: 0014D6:	26 40      	4026     	bne     0x0014DC
	assert_assembly('bne     0x0014DC', [0x26, 0x40], pc=0x0014D6)
	
	#@FIXME: Weird output! 0x5E instead of 0x4x
	# Test: 0014E4:	F8 5E      	5EF8     	ble     0x0014EC
	assert_assembly('ble     0x0014EC', [0xf8, 0x5e], pc=0x0014E4)
	
	# Test: 001720:	EA 40      	40EA     	ble     0x00172A
	assert_assembly('ble     0x00172A', [0xea, 0x40], pc=0x001720)
	
	# Test: 0014EA:	80 42      	4280     	bhi     0x00150A
	assert_assembly('bhi     0x00150A', [0x80, 0x42], pc=0x0014EA)
	# Test: 0014F0:	3A 41      	413A     	bfc     0x00150A
	assert_assembly('bfc     0x00150A', [0x3a, 0x41], pc=0x0014F0)
	
	# Switch-a-roo: So similar, but so different...
	# Test: 00108E:	64 40      	4064     	bcc     0x001092
	assert_assembly('bcc     0x001092', [0x64, 0x40], pc=0x00108E)
	# Test: 001096:	76 5E      	5E76     	bcc     0x0010A0
	assert_assembly('bcc     0x0010A0', [0x76, 0x5e], pc=0x001096)
	
	# Test: 00294E:	30 6E      	6E30     	sne     r8
	assert_assembly('sne     r8', [0x30, 0x6e])
	# Test: 024E72:	00 6E      	6E00     	seq     r0
	assert_assembly('seq     r0', [0x00, 0x6e])
	# Test: 0027B6:	04 6E      	6E04     	seq     r2
	assert_assembly('seq     r2', [0x04, 0x6e])
	
	#asm.dump()
	put('All tests OK')

def test_reassemble():
	"""Take a known disassembly and try to re-assemble it. Compare against previous binary"""
	
	filename = '/z/data/_code/_c/V-Tech/vcxdk.git/tools/cr16b_dasm/ROM_GL8008CX_27-6393-11.asm'
	put('Self-test against disassembly file "%s"...' % filename)
	with open(filename, 'r') as h:
		data = h.read()
	
	lines = data.split('\n')
	for l in lines:
		l = l.strip()
		if l == '': continue
		if l[:1] == ';': continue
		
		# Split into OFS, BYTES, WORDS, ASM
		parts = l.split('\t')
		if len(parts) < 4: continue	# Must have at least 4 tab delimited columns (OFS, BYTES, WORD, ASM)
		if parts[0][-1:] != ':': continue	# Must start with 000OFS:
		#put(l)
		
		pc = int(parts[0][:-1], 16)
		bin = [ int(hexb,16) for hexb in parts[1].strip().split(' ') ]
		asm = parts[3]
		#try:
		assert_assembly(asm, bin, pc=pc)
		#except AssertionError as e:
		#	put('! DIFFERENCE: %s' % str(e))
	

def test_manual_assembly():
	"""Assemble by manually calling each method"""
	asm = CR16B_Assembler()
	#asm.pc = 0x200
	#asm.assemble_movw(0xb700, REG_SP)	# movw    $0xB700, sp
	asm.assemble_basic_imm_reg_medium(op=OP_MOV, i=I_WORD, imm16=0xb700, dest_reg=REG_SP)
	asm.assemble_push(reg=REG_R0, count=2)	# push    $2, r0
	asm.assemble_movd(0x189E91, REG_R4)	# movd    $0x189E91, (r5,r4)
	asm.assemble_movd(0x18AB57, REG_R2)	# movd    $0x18AB57, (r3,r2)
	asm.assemble_bal(0x1805c4)	# bal     (ra,era), 0x1805c4
	asm.assemble_basic_imm_reg_short(op=OP_ADDU, i=I_WORD, imm5=4, dest_reg=REG_SP)	# adduw   $0x4, sp
	asm.assemble_basic_imm_reg_short(op=OP_CMP, i=I_BYTE, imm5=1, dest_reg=REG_R0)	# cmpb    $0x1, r0
	#asm.assemble_bne(disp=0x16)
	asm.assemble_br(cond=COND_NE, disp=0x16)
	asm.dump()

def test_text_parser():
	"""Assemble using a text listing"""
	
	asm = CR16B_Assembler()
	asm.assemble("""
	.foo:
		movw $0xb700, sp
		push $2, r0
		movd    $0x189E91, (r5,r4)	; 9E91 = "Achtung! Kassette beenden! (J/N)?"
		movd    $0x18AB57, (r3,r2)	; AB57 = "Schuetzt die Erde!"
		bal     (ra,era), 0x1805c4
		adduw   $0x4, sp
		cmpb    $0x1, r0
		bne     0x22c
		
		br .foo
	""", pc=0x200)
	asm.dump()


### Patch helpers
def copy_file(filename_src, filename_dst, ofs=0, size=-1):
	with open(filename_src, 'rb') as h:
		h.seek(ofs)
		if size <= 0: data = h.read()	# All
		else: data = h.read(size)
	
	with open(filename_dst, 'wb') as h:
		h.write(data)
	

def patch_file(filename, ofs, data):
	with open(filename, 'rb') as h:
		data_old = h.read()
	
	data2 = data_old[:ofs] + data + data_old[ofs + len(data):]
	
	with open(filename, 'wb') as h:
		#h.seek(ofs)
		#h.write(data)
		h.write(data2)

def run_patch():
	"""Patch a ROM"""
	filename_src = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update.dump.000.seg0-64KB__4KB_used.bin'
	filename_dst = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update_hacked.8KB.bin'
	
	# Create a copy
	copy_file(filename_src, filename_dst, ofs=0, size=8192)
	
	
	# Add some strings
	#@TODO: Use assembly for that: "ofs 0xXXXX" and "db 'something'"
	#patch_file(filename_dst, ofs=0x0c00, data=b'HotKey was here!\x00')
	#patch_file(filename_dst, ofs=0x0c40, data=b'HACKED!\x00')
	
	
	# Patch all potential entry points
	#ofs = 0x000200
	ofs = 0	# We byte-bang the full header of the "Update Cart" ROM
	
	text = """
; Cartridge header (VTECHCARTRIDGE, ONBOARDCARTRIDGE, TESTHWCART)
	db      'VTECHCARTRIDGE'
	db      0x00, 0x00
	db      0xed, 0x01
	db      '016959'
	db      0x00, 0x02, 0x01, 0x00, 0x50, 0x00, 0x00, 0x00, 0x00, 0x00
	db      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x51, 0x00, 0x00, 0x00, 0x00, 0x00
	db      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
	db      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04
	db      0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04
	db      0x00, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04
	db      0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04
	db      0x00, 0x00, 0x02, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05
	db      0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05
	db      0x00, 0x00, 0x03, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05
	db      0x00, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05
	db      0x00, 0x00, 0x05, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05
	db      0x00, 0x00, 0x02, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03
	db      0x00, 0x00, 0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04
	db      0x00, 0x00, 0x03, 0x00, 0x02, 0x00
	

; DATA: Const data
ofs 0x180
.str_hello:
	db      'Hello world!',0x00
.str_htk:
	db      'HotKey was truly here!',0x00


; TEXT: Actual code (at offset 0x200)
ofs 0x200	; Hard-coded entry point when invoking the cartridge
_main:
	push    $2, era
	
.start:
	
	
	; For some reason the dialogs aren't visible in main menu.
	; However, just enter the FileManager before pressing the cartridge button.
	
	
	
	; Show a prompt (Y/N)
	movd    $0x034191, (r1,r0)	; Dunno what this param does...
	push    $2, r0
	
	;OK!	movd    $0x100B18, (r5,r4)	; 00B18 = STRING "028100"
	;OK!	movd    $0x100c40, (r3,r2)	; my own patched string with added ROM base offset (0x100000)
	;OK!	movd    $0x100c00, (r5,r4)	; my own patched string with added ROM base offset (0x100000)
	movd    .str_hello, (r3,r2)	; Use our own constant
	adduw   $0x10, r3	; Add the cartridge ROM base address (0x100000)
	movd    .str_htk, (r5,r4)	; Use our own constant
	adduw   $0x10, r5	; Add the cartridge ROM base address (0x100000)
	
	bal     (ra,era), 0x1805C4	; prompt_yesno__title_r3r2__text_r5r4__sys5c4 (0x0005C4 + internal ROM offset 0x180000)
	adduw   $0x4, sp
	
	; Check the result in r0
	cmpb    $0x1, r0	; 1 = YES, 0 = NO
	beq     .start	; Back to start
	;beq     .end	; Exit out
	
	
	; Show an alert
	;	027908:	12 64 71 51	6412 5171	movd    $0x035171, (r1,r0)
	;	02790C:	F8 23      	23F8     	adduw   $-0x8, sp
	;	02790E:	1E E4      	E41E     	storw   r0, 0x4(sp)
	;	027910:	3E E6      	E63E     	storw   r1, 0x6(sp)
	;	027912:	1F 78      	781F     	movw    sp, r0
	;	027914:	11 22 32 00	2211 0032	adduw   $0x32, r0
	;	027918:	20 38      	3820     	movw    $0, r1
	;	02791A:	1E E0      	E01E     	storw   r0, 0(sp)
	;	02791C:	3E E2      	E23E     	storw   r1, 0x2(sp)
	;	02791E:	81 18      	1881     	movb    $0x01, r4
	;	...
	;	02793E:	48 64 D7 98	6448 98D7	movd    $0x0898D7, (r3,r2)	; 0x0898D7 = STRING "Alarm"
	;	027942:	BE 77 D7 13	77BE 13D7	bal     (ra,era), 0x018D18
	;	027946:	E8 23      	23E8     	adduw   $0x8, sp
	;	027948:	BC 77 DD 8A	77BC 8ADD	bal     (ra,era), 0x000424
	
	movd    $0x035171, (r1,r0)	; Dunno what this param does
	adduw   $-0x8, sp
	storw   r0, 0x4(sp)
	storw   r1, 0x6(sp)
	movw    sp, r0
	adduw   $0x32, r0
	movw    $0, r1
	storw   r0, 0(sp)
	storw   r1, 0x2(sp)
	movb    $0x01, r4
	
	;movd    $0x0898D7, (r3,r2)	; 0x0898D7 = STRING "Alarm"
	movd    .str_htk, (r3,r2)	; Use our own constant
	adduw   $0x10, r3	; Add the cartridge ROM base address (0x100000)
	
	bal     (ra,era), 0x198D18	; 0x018D18 + 0x180000
	adduw   $0x8, sp
	bal     (ra,era), 0x180424	; 0x000424 + 0x180000
	
	
	
	; Show a popup
	movd    $0x034191, (r1,r0)	; Dunno what this param does
	adduw   $-0x8, sp
	storw   r0, 0x4(sp)
	storw   r1, 0x6(sp)
	
	;???	movd    $0x18AB57, (r1,r0)	; AB57 = "Schuetzt die Erde!"
	;???	movd    0x100AD2, (r1,r0)	; 00AD2 = STRING "Update Programm-Zusatzkassette"
	;OK!	movd    0x100c00, (r1,r0)	; Use the patched-in string + base address (0x100000)
	movd    .str_htk, (r1,r0)	; Use our own constant
	adduw   $0x10, r1	; Add the cartridge ROM base address (0x100000)
	
	storw   r0, 0(sp)
	storw   r1, 0x2(sp)
	
	movb    $0, r4
	movd    $0x084D40, (r3,r2)	; Dunno what this param does
	bal     (ra,era), 0x198CC4	; show_info_popup_r1r0 (0x018CC4 + internal ROM offset 0x180000)
	adduw   $0x8, sp
	
	
	
	; Ask for a string?
	;	030D10:	12 64 91 41	6412 4191	movd    $0x034191, (r1,r0)
	;	030D14:	F8 23      	23F8     	adduw   $-0x8, sp
	;	030D16:	1E E4      	E41E     	storw   r0, 0x4(sp)
	;	030D18:	3E E6      	E63E     	storw   r1, 0x6(sp)
	;	030D1A:	08 64 75 9A	6408 9A75	movd    $0x089A75, (r1,r0)	; 0x089A75 = STRING "Gib deinen Namen ein!"
	;	030D1E:	1E E0      	E01E     	storw   r0, 0(sp)
	;	030D20:	3E E2      	E23E     	storw   r1, 0x2(sp)
	;	030D22:	80 18      	1880     	movb    $0, r4
	;	030D24:	48 64 C2 4F	6448 4FC2	movd    $0x084FC2, (r3,r2)
	;	030D28:	AE 77 9D 7F	77AE 7F9D	bal     (ra,era), 0x018CC4	; show_info_popup_r1r0
	;	030D2C:	7F B8 44 7D	B87F 7D44	loadw   0x07D44, r3
	;	030D30:	9F B8 46 7D	B89F 7D46	loadw   0x07D46, r4
	;	
	
	; Ask for a number?
	;	031298:	48 64 7F 99	6448 997F	movd    $0x08997F, (r3,r2)	; 0x08997F = STRING "Zahleneingabe"
	;	03129C:	BE 77 B9 EB	77BE EBB9	bal     (ra,era), 0x02FE54
	

.end:
	; Exit/Reboot
	;popret  $2, era
	;pop  $2, era
	;jump    (ra,era)
	bal     (ra,era), 0x180000	; Reboot


.halt_loop:
	br      .halt_loop
	

_delay:
	push    $2, era
	; Delay
	movw    $0x7ff0, r0
.delay_loop:
	nop
	nop
	nop
	nop
	subw    $1, r0
	cmpw    $0, r0
	bne     .delay_loop
	popret  $2, era
	"""
	
	asm = CR16B_Assembler()
	bin = asm.assemble(pc=ofs, text=text)
	asm.dump()
	
	put('Patching file at offset 0x%06X (%d bytes)...' % (ofs, len(bin)))
	patch_file(filename_dst, ofs=ofs, data=bin)
	
	put('Patch done.')
	


if __name__ == '__main__':
	#import sys
	#
	#if len(sys.argv) < 2:
	#	put('No argument given, running test(s)...')
		
	# Enable what to do, e.g. do assembler self-tests or actually try assembling and patching something
	#test_manual_assembly()
	#test_text_parser()
	#test_instructions()
	test_reassemble()
	
	#run_patch()
	
	