#!/usr/bin/python3
"""
National Semiconductors
CR16A/CR16B not-yet-assembler

(at least a tool for helping me patch some bytes in the ROM)


2022-04-20 Bernhard "HotKey" Slawik
"""

def put(t):
	print(t)

class DataStore:
	def __init__(self):
		self.data = []
	
	def clear(self):
		self.data = []
	
	def w8(self, v8):
		self.data.append(v8)
	
	def w16(self, v16):
		self.w8( v16 & 0x000000ff)
		self.w8((v16 & 0x0000ff00) >> 8)
		
	def w32(self, v32):
		self.w8( v32 & 0x000000ff)
		self.w8((v32 & 0x0000ff00) >> 8)
		self.w8((v32 & 0x00ff0000) >> 16)
		self.w8((v32 & 0xff000000) >> 24)
	
	def get_data(self):
		return self.data
	def get_bytes(self):
		return bytes(self.data)

I_BYTE = 0
I_WORD = 1

# The op value changes according to format (e.g. w/cw/uw)
# u = +1, c = +8
OP_ADD = 0b0000	# addX
OP_ADDU = 0b0001	# adduX
OP_ADDC = 0b1001	# addcX
OP_SUB = 0b1111	# subX
OP_SUBU = 0b0110	# subuX
OP_SUBC = 0b1101	# subcX
OP_CMP = 0b0111
OP_MOV = 0b1100	# movX

OP_PUSH = 0b0110
OP_POP = 0b0110	# Same as PUSH! But param differs
OP_POPRET = 0b0110	# Same as PUSH! But param differs

# List of basic 3-letter mnemonics that can be all handled the same way
OP_BASICS = {
	'mov': OP_MOV,
	
	'add': OP_ADD,
	'addu': OP_ADDU,
	'addc': OP_ADDC,
	
	'sub': OP_SUB,
	'subu': OP_SUBU,
	'subc': OP_SUBC,
	
	'cmp': OP_CMP,
}

REG_R0 = 0
REG_R1 = 1
REG_R2 = 2
REG_R3 = 3
REG_R4 = 4
REG_R5 = 5
REG_R6 = 6
REG_R7 = 7
REG_R8 = 8
REG_R9 = 9
REG_R10 = 10
REG_R11 = 11
REG_R12 = 12
REG_R13 = 13	# ERA = R13
REG_ERA = 13	# ERA = R13
REG_RA = 14
REG_SP = 15

def str_to_reg(reg):
	if reg == 'era': return REG_ERA
	elif reg == 'ra': return REG_RA
	elif reg == 'sp': return REG_SP
	elif reg[:1] == 'r': return int(reg[1:])
	raise KeyError('Unknown register "%s"' % reg)


# Dedicated CPU Registers
R_PSR = 0b0001
R_CFG = 0b0101
R_INTBASEL = 0b0011
R_INTBASEH = 0b0100
R_ISP = 0b1011
R_DSR = 0b0111
R_DCR = 0b1001
R_CARL = 0b1101
R_CARH = 0b1110

COND_EQ = 0b0000
COND_NE = 0b0001
COND_GE = 0b1101
COND_CS = 0b0010
COND_CC = 0b0011
COND_HI = 0b0100
COND_LS = 0b0101
COND_LO = 0b1010
COND_HS = 0b1011
COND_GT = 0b0110
COND_LE = 0b0111
COND_FS = 0b1000
COND_FC = 0b1001
COND_LT = 0b1100

class CR16B_Assembler:
	def __init__(self, pc=0x000000):
		self.stor = DataStore()
		self.pc = pc
		self.labels = {}
	
	def w_raw(self, v):
		if type(v) is list:
			for w in v:
				self.stor.w8(w)
				self.pc += 1
		else:
			self.stor.w8(v)
	def w8(self, v8):
		self.stor.w8(v8)
		self.pc += 1
	def w16(self, v16):
		self.stor.w16(v16)
		self.pc += 2
	def w32(self, v32):
		self.stor.w32(v32)
		self.pc += 4
	def get_data(self):
		return self.stor.get_data()
	
	def dump(self):
		"""Output data store"""
		put(' '.join(['%02X'%b for b in self.stor.get_data()]))
	
	def clear(self):
		self.stor.clear()
		self.labels = {}
	
	def assemble(self, text, pc=None):
		"""Dirty assembly text parser"""
		
		if pc is None:
			pc = self.pc
		
		for line in text.split('\n'):
			#put('Parsing "%s"' % line)
			
			# Clean and filter
			if ';' in line: line = line[:line.index(';')]
			line = line.replace('\t', ' ')
			line = line.replace(', ', ',')
			line = line.replace('    ', ' ')
			line = line.replace('  ', ' ')
			line = line.replace('  ', ' ')
			line = line.strip().lower()
			if line == '': continue
			
			# Parse mnemonic and parameters
			words = line.split(' ')
			mnem = words[0]
			
			# Remember labels
			if mnem[-1:] == ':':
				#put('Remembering label "%s" as pc=0x%06X...' % (mnem[:-1], self.pc))
				self.labels[mnem[:-1]] = self.pc
				continue
			
			# Parse remainder
			p = '' if len(words) < 2 else words[1]
			
			# Split parameters
			params = []
			while len(p) > 0:
				#put('"%s"' % p)
				# Find parameter delimiter
				try:
					if p[:1] == '(':	# Handle nested commas, e.g. "(ra,era)" etc.
						o = p.index(',', p.index(')'))
					else:
						o = p.index(',')
				except ValueError:
					o = len(p)
				
				# Get the first remaining word
				w = p[:o]
				
				# Handle immediates and addresses
				#@FIXME: Negative numbers etc.!
				if (w[:3] == '$0x'): params.append(int(w[1:], 16))
				elif (w[:1] == '$'): params.append(int(w[1:]))
				elif (w[:2] == '0x'): params.append(int(w,16))
				elif (w[:1] == ':'):
					#put('Looking up label "%s"...' % w[1:])
					params.append(self.labels[w[1:]])
				else:
					# Remember "as-is"
					params.append(w)
				
				# Continue with next param
				p = p[o+1:]
			
			# Handle mnemonics
			#put('%s	%s' % (mnem, str(params)))
			
			if mnem == 'movd':	# movd is a special case
				self.assemble_movd(params[0], str_to_reg(params[1][1:-1].split(',')[1]))
			
			elif mnem[:-1] in OP_BASICS:
				# Handle all "basic" mnemonics the same way
				
				op = OP_BASICS[mnem[:-1]]
				
				#@FIXME: adduw VS. addw VS. addcw: b, cb, w, cw, uw
				form = mnem[-1:]
				
				if form == 'b': i = I_BYTE
				elif form == 'w': i = I_WORD
				else:
					raise TypeError('Unknown format identifier "%s" in mnemonic "%s"!' % (form, mnem))
				
				dest_reg = str_to_reg(params[1])
				
				if type(params[0]) is int:
					imm = params[0]
					self.assemble_basic_imm_reg(op=op, i=i, imm=imm, dest_reg=dest_reg)
				else:
					src_reg = str_to_reg(params[0])
					self.assemble_basic_reg_reg(op=op, i=i, src_reg=src_reg, dest_reg=dest_reg)
			
			elif mnem == 'push':
				self.assemble_push(count=params[0], reg=str_to_reg(params[1]))
			elif mnem == 'pop':
				self.assemble_pop(count=params[0], reg=str_to_reg(params[1]))
			elif mnem == 'popret':
				self.assemble_popret(count=params[0], reg=str_to_reg(params[1]))
			
			elif mnem == 'bal':
				self.assemble_bal(dest=params[1], lnk_pair=str_to_reg(params[0][1:-1].split(',')[1]))
			
			elif mnem == 'beq0b':
				asm.assemble_brcond(cond=COND_EQ, val1=0, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - self.pc)
			elif mnem == 'beq1b':
				asm.assemble_brcond(cond=COND_EQ, val1=1, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - self.pc)
			elif mnem == 'bne0b':
				asm.assemble_brcond(cond=COND_NE, val1=0, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - self.pc)
			elif mnem == 'bne1b':
				asm.assemble_brcond(cond=COND_NE, val1=1, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - self.pc)
				
			elif mnem == 'br':
				self.assemble_br(cond=COND_EQ, disp=params[0] - self.pc)
			elif mnem == 'beq':
				self.assemble_br(cond=COND_EQ, disp=params[0] - self.pc)
			elif mnem == 'bne':
				self.assemble_br(cond=COND_NE, disp=params[0] - self.pc)
			
			elif mnem == 'jump':
				self.assemble_jump(reg_pair=str_to_reg(params[0][1:-1].split(',')[1]))
			
			else:
				raise KeyError('Mnemonic "%s" not part of the *very* limited set of supported OpCodes!' % mnem)
			
		#
		
		return self.stor.get_bytes()
	
	def assemble_basic_reg_reg(self, op, i, src_reg, dest_reg):
		"""Basic instruction involving two registers"""
		
		# 01 at 15..14
		# i at 13
		# op at 12..9
		instr16 = \
			  (0b01 << 14)\
			| (i << 13)\
			| (op << 9)\
			| (dest_reg << 5)\
			| (src_reg << 1)\
			| 1
		
		# [ (instr & 0x000000ff), ((instr & 0x0000ff00) >> 8) ]
		self.w16(instr16)
	
	
	def assemble_basic_imm_reg(self, op, i, imm, dest_reg):
		"""Basic instruction involving an immediate and a register. Automatically handles the size."""
		
		#@FIXME: Need to check unsigned/signed
		
		#@FIXME: According to the manual the only allowed values for imm5 are: -16, -14...15 (note: no -15 !)
		if imm < 16:
			self.assemble_basic_imm_reg_short(op, i, imm, dest_reg)
		else:
			self.assemble_basic_imm_reg_medium(op, i, imm, dest_reg)
	
	def assemble_basic_imm_reg_short(self, op, i, imm5, dest_reg):
		"""Basic instruction involving a short 5-bit immediate and a register."""
		
		self.w16(
			  (0b00 << 14)\
			| (i << 13)\
			| (op << 9)\
			| (dest_reg << 5)\
			| imm5
		)
	
	def assemble_basic_imm_reg_medium(self, op, i, imm16, dest_reg):
		"""Basic instruction involving a medium 16-bit immediate and a register."""
		
		self.w32(
			  (imm16 << 16)\
			| (0b00 << 14)\
			| (i << 13)\
			| (op << 9)\
			| (dest_reg << 5)\
			| 0b10001
		)
	
	#def assemble_movw(self, imm16, dest_reg):
	#	self.assemble_basic_imm_reg_medium(op=OP_MOV, i=I_WORD, imm16=imm16, dest_reg=dest_reg)
	
	def assemble_brcond(self, cond, val1, i, reg, disp5m1):
		"""Assemble Compare-and-Branch (BEQ0/1i, BNE0/1i)"""
		
		
		self.w16(
			  (i << 13)\
			| (0xa << 9)\
			| (((reg & 0b1000) >> 3) << 8)\
			| (cond << 7)\
			| (val1 << 6)\
			| ((reg & 0b0001) << 5)\
			| (((disp5m1 & 0b11110) >> 1) << 1)\
			| 1
		)
	
	def assemble_movd(self, imm21, dest_pair):
		"""Assemble special case MOVD which involves a register pair as destination.
		
			dest_pair: index of the lower reg (e.g. 0 for r1,r0)
				0b0000 = r1,r0
				0b0001 = r2,r1
				0b0010 = r3,r2
				0b0011 = r4,r3
				0b0100 = r5,r4
		"""
		
		instr32 = \
			  ((imm21 & 0b000001111111111111111) << 16)\
			| (0b011001 << 10)\
			| (((imm21 & 0b100000000000000000000) >> 20) << 9)\
			| (dest_pair << 5)\
			| (((imm21 & 0b000010000000000000000) >> 16) << 4)\
			| (((imm21 & 0b011100000000000000000) >> 17) << 1)
		
		#[ (instr & 0x000000ff), ((instr & 0x0000ff00) >> 8), ((instr & 0x00ff0000) >> 16), ((instr & 0xff000000) >> 24) ]
		self.w32(instr32)
	
	
	def assemble_special(self, op, p1=0, p2=0):
		"""Assemble instructions that contain no/little parameters.
		
			DI, EI, EXCP, LPR, MOVXB, MOVZB, RETX
			Scond, SPR, EIWAIT, MULSW, MULUW, MULSB, PUSH, POPrt, LOADM, STORM, WAIT
		"""
		
		self.w16(
			  (0b011 << 13)\
			| (op << 9)\
			| (p1 << 5)\
			| (p2 << 1)
		)
	
	def assemble_push(self, reg, count=1):
		# Note: Rcnt = count-1
		self.assemble_special(op=OP_PUSH, p1=count -1, p2=reg)
	def assemble_pop(self, reg, count=1):
		# Note: Rcnt = count-1
		self.assemble_special(op=OP_POP, p1=0b100 + count -1, p2=reg)
	
	def assemble_popret(self, reg, count=1):
		# Note: Rcnt = count-1
		#self.assemble_special(op=OP_POPRET, p1=0x04 + count -1, p2=reg)
		self.w16(
			  (0b011011011 << 7)\
			| ((count-1) << 5)\
			| (reg << 1)
		)
	
	#@TODO: LOADi, STORi
	
	def assemble_br(self, disp, cond=0x0e):
		"""Assemble a branch with condition with given displacement, automatically choses the instruction size.
			cond:
				1=NE
				
				0xe=no condition
		"""
		
		if disp < 0:
			# Backwards
			#@FIXME: This is doen by trial and error
			self.assemble_br_medium(disp=disp + 0x200000, cond=0x0e)
		elif (disp < 0b1000000000):
			self.assemble_br_short(disp=disp, cond=cond)
		else:
			self.assemble_br_medium(disp=disp, cond=cond)
	
	
	def assemble_br_short(self, disp, cond=0):
		
		if (disp >= 0b1000000000): raise ValueError('displacement too big for short br')
		
		self.w16(
			  (0b010 << 13)\
			| (((disp & 0b111100000) >> 5) << 9)\
			| (cond << 5)\
			| ((disp & 0b000011111))
		)
	
	def assemble_br_medium(self, disp, cond=0):
		# Medium, Large Memory Model
		self.w32(
			  (((disp & 0b000001111111111111110) >> 1) << 17)\
			| (((disp & 0b100000000000000000000) >> 20) << 16)\
			| (0b0111010 << 9)\
			| (cond << 5)\
			| (((disp & 0b000010000000000000000) >> 16) << 4)\
			| (((disp & 0b011100000000000000000) >> 17) << 1)
		)
	
	#def assemble_bne(self, disp):
	#	#self.w16(0x4020 + disp)
	#	self.assemble_br(cond=COND_NE, disp=disp)
	
	def assemble_bal(self, dest, lnk_pair=REG_ERA, pc=None):
		"""Assemble branch and link for Large Memory Model.
		lnk_pair: 0=r1,r0, 1=r2,r1, ... 13 = 0b1101 = ra,era (R13), 14=RA, 15=SP"""
		
		if pc is None:
			pc = self.pc
		
		disp = dest - pc
		
		# BAL (ra, era) - CR16B Large Memory Format
		#	d15..d1 at 31..17
		#	d20 at 16
		#	const at 15..9	(0b0111011 for "bal")
		#	lnk-pair at 8..5	(0b1101 = 13 for "ra,era")
		#	d16 at 4
		#	d19..d17 at 1
		#             d:098765432109876543210
		instr32 = \
			  (((disp & 0b000001111111111111110) >> 1) << 17)\
			| (((disp & 0b100000000000000000000) >> 20) << 16)\
			| (0b0111011 << 9)\
			| (lnk_pair << 5)\
			| (((disp & 0b000010000000000000000) >> 16) << 4)\
			| (((disp & 0b011100000000000000000) >> 17) << 1)
		
		#[ (instr & 0x000000ff), ((instr & 0x0000ff00) >> 8), ((instr & 0x00ff0000) >> 16), ((instr & 0xff000000) >> 24) ]
		self.w32(instr32)
	
	
	def assemble_jump(self, reg_pair=REG_ERA, cond=0x06):
		self.w16(
			  (0b00010111 << 8)\
			| (cond << 5)\
			| (reg_pair << 1)\
			| 1
		)
	
	#@TODO: JAL
	
	#@TODO: Bit manipulation
	

### Tests
def assert_assembly(text, bin, pc=0x0000):
	put('Checking "%s" =?= %s' % (text, ' '.join([ '%02X' % b for b in bin]) ))
	
	asm = CR16B_Assembler()
	asm.assemble(text, pc=pc)
	bin2 = asm.get_data()
	
	#asm.dump()
	
	assert len(bin) == len(bin2), 'Assembled binary sizes differs!'
	
	for i in range(len(bin)):
		assert bin2[i] == bin[i], 'Binary difference at [%d]: 0x%02X != 0x%02X in binary output %s' % (i, bin2[i], bin[i], ' '.join([ '%02X' % b for b in bin2]))
	
	#put('Okay!')
	return True

def test_equality():
	"""Compare assembled code to known binary output"""
	
	asm = CR16B_Assembler()
	
	# Test MOVD
	# Test: 000682:	00 66 98 09	6600 0998	movd    $0x100998, (r1,r0)
	#asm.assemble_movd(imm21=0x100998, dest_pair=0b0000)
	# Test: 0004AC:	20 66 FA 09	6620 09FA	movd    $0x1009FA, (r2,r1)
	#asm.assemble_movd(imm21=0x1009FA, dest_pair=0b0001)
	# Test: 0004C6:	4C 66 00 00	664C 0000	movd    $0x1C0000, (r3,r2)
	#asm.assemble_movd(imm21=0x1C0000, dest_pair=0b0010)
	# Test: 000588:	80 66 0C 0B	6680 0B0C	movd    $0x100B0C, (r5,r4)
	#asm.assemble_movd(imm21=0x100B0C, dest_pair=0b0100)
	
	# Test BAL
	# 00006E:	B2 77 90 35	77B2 3590	bal     (ra,era), 0x0335FE
	#asm.assemble_bal(pc = 0x00006E, dest = 0x0335FE)
	# 0021EC:	A0 77 34 03	77A0 0334	bal     (ra,era), 0x002520
	#asm.assemble_bal(pc = 0x0021EC, dest = 0x002520)
	# 0034BA:	BE 77 CB E4	77BE E4CB	bal     (ra,era), 0x001984
	#asm.assemble_bal(pc = 0x00006E, dest = 0x0335FE)
	# 033CAC:	A0 77 26 04	77A0 0426	bal     (ra,era), 0x0340D2
	#asm.assemble_bal(pc = 0x00006E, dest = 0x0335FE)
	# Test: Update Cart: 0006FA:	B6 77 9F FD	77B6 FD9F	bal     (ra,era), 0x180498
	#asm.assemble_bal(pc=0x0006FA, dest=0x180498)
	#asm.assemble_bal(pc=0x00020E, dest=0x1805c4)
	#asm.assemble_bal(pc=0x000222, dest=0x1805c4)
	#asm.assemble_bal(pc=0x000538, dest=0x018D18)
	
	# Test POP/POPRET
	# Test: 00041A:	BA 6D      	6DBA     	popret  $2, era ; LMM
	#asm.assemble_popret(reg=REG_ERA, count=2)	# popret  $2, era ; LMM
	# Test: 000458:	EE 6C      	6CEE     	pop     $4, r7
	#asm.assemble_pop(reg=REG_R7, count=4)	# pop     $4, r7
	# Test: 000928:	96 6C      	6C96     	pop     $1, r11
	#asm.assemble_pop(reg=REG_R11, count=1)	# pop     $1, r11
	
	# Test: JUMP
	# Test: 001026:	DB 17      	17DB     	jump    (ra,era)
	#asm.assemble_jump(reg_pair=REG_ERA)	# jump    (ra,era)
	
	# Test: Simple branch
	# Test: 000304:	C2 75 CC F6	75C2 F6CC	br      0x02F9D0
	#asm.assemble_br(disp=(0x02F9D0 - 0x000304))	#, cond=0x0e)
	
	# Test: 03385C:	DE 75 07 FF	75DE FF07	br      0x033762
	#asm.assemble_br(disp=(0x033762 - 0x03385C))
	
	# Test: Compare-and-Branch
	##@FIXME: This does not work!
	## Test: 015946:	1D 14      	141D     	beq0b   r0, 0x01594A
	##asm.assemble_beq(op=0xe, opext=3, i=I_BYTE, reg=REG_R0, imm4m1=(0x01594A - 0x015946))
	# Test: 03194A:	09 15      	1509     	beq0b   r8, 0x031952
	#asm.assemble_brcond(cond=COND_EQ, val1=0, i=I_BYTE, reg=REG_R8, disp5m1=(0x031952 - 0x03194A))
	# Test: 031964:	49 15      	1549     	beq1b   r8, 0x03196C
	#asm.assemble_brcond(cond=COND_EQ, val1=1, i=I_BYTE, reg=REG_R8, disp5m1=(0x03196C - 0x031964))
	# Test: 015412:	8D 14      	148D     	bne0b   r0, 0x01541E	; back to loop
	#asm.assemble_brcond(cond=COND_NE, val1=0, i=I_BYTE, reg=REG_R0, disp5m1=(0x1541E - 0x015412))
	# Test: 015904:	CB 14      	14CB     	bne1b   r0, 0x01590E
	#asm.assemble_brcond(cond=COND_NE, val1=1, i=I_BYTE, reg=REG_R0, disp5m1=(0x01590E - 0x015904))
	
	
	# Test add/sub with different format qualifiers
	
	# Test: 0020FA:	00 00      	0000     	addb    $0, r0
	assert_assembly('addb    $0, r0', [0x00, 0x00])
	# Test: 03301C:	60 13      	1360     	addcb   $0, r11
	assert_assembly('addcb   $0, r11', [0x60, 0x13])
	# Test: 03443C:	01 02      	0201     	addub   $0x1, r0
	assert_assembly('addub   $0x1, r0', [0x01, 0x02])
	# Test: 001094:	89 60      	6089     	addw    r4, r4
	assert_assembly('addw    r4, r4', [0x89, 0x60])
	# Test: 001F14:	31 22 00 10	2231 1000	adduw   $0x1000, r1
	assert_assembly('adduw   $0x1000, r1', [0x31, 0x22, 0x00, 0x10])
	# Test: 001F18:	40 32      	3240     	addcw   $0, r2
	assert_assembly('addcw   $0, r2', [0x40, 0x32])
	# Test: 001092:	01 72      	7201     	addcw   r0, r0
	assert_assembly('addcw   r0, r0', [0x01, 0x72])
	
	# Test: 002A2A:	02 1E      	1E02     	subb    $0x2, r0
	assert_assembly('subb    $0x2, r0', [0x02, 0x1E])
	# Test: 00204A:	A1 3E      	3EA1     	subw    $0x1, r5
	assert_assembly('subw    $0x1, r5', [0xA1, 0x3E])
	# Test: 00204C:	C0 3A      	3AC0     	subcw   $0, r6
	assert_assembly('subcw   $0, r6', [0xc0, 0x3a])
	
	
	#asm.dump()
	put('All OK')


def test_manual_assembly():
	"""Assemble by manually calling each method"""
	asm = CR16B_Assembler()
	asm.pc = 0x200
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

def test_text_assembly():
	"""Assemble using a text listing"""
	
	asm = CR16B_Assembler(pc=0x200)
	asm.assemble("""
	foo:
		movw $0xb700, sp
		push $2, r0
		movd    $0x189E91, (r5,r4)	; 9E91 = "Achtung! Kassette beenden! (J/N)?"
		movd    $0x18AB57, (r3,r2)	; AB57 = "Schuetzt die Erde!"
		bal     (ra,era), 0x1805c4
		adduw   $0x4, sp
		cmpb    $0x1, r0
		bne     0x22c
		
		br :foo
	""")
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

def test_patch():
	"""Patch a ROM"""
	filename_src = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update.dump.000.seg0-64KB__4KB_used.bin'
	filename_dst = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update_hacked.8KB.bin'
	
	# Create a copy
	copy_file(filename_src, filename_dst, ofs=0, size=8192)
	
	# Patch it
	ofs = 0x100
	bin = asm.assemble(pc=ofs, text="""
	
	""")
	
	put('Patching at offset 0x%06X (%d bytes)...' % (ofs, len(bin)))
	patch_file(filename_dst, ofs=ofs, data=bin)
	
	
	
	text = """
		;movw $0xb700, sp
		
		;push    $2, era
		;bal (ra, era), 0x100	; Call the code above
		;pop     $2, era
		
		push    $2, era
		
		movd    $0x034191, (r1,r0)	; Dont know why
		push $2, r0
		movd    $0x189E91, (r5,r4)	; 9E91 = "Achtung! Kassette beenden! (J/N)?"
		movd    $0x18AB57, (r3,r2)	; AB57 = "Schuetzt die Erde!"
		bal     (ra,era), 0x1805C4	; prompt_yesno__title_r3r2__text_r5r4__sys5c4
		adduw   $0x4, sp
		;cmpb    $0x1, r0
		;bne     0x22c
		
		;popret   $2, era
		
		pop     $2, era
		jump    (ra,era)
	"""
	
	# Patch all potential entry points
	ofss = [
		0x000200,
		0x000400,
		0x00041C,
		0x00045C,
		0x00051C,
		0x000542
	]
	for ofs in ofss:
		asm = CR16B_Assembler()
		bin = asm.assemble(pc=ofs, text=text)
		asm.dump()
		
		put('Patching at offset 0x%06X (%d bytes)...' % (ofs, len(bin)))
		patch_file(filename_dst, ofs=ofs, data=bin)
	


if __name__ == '__main__':
	
	test_equality()
	
	#test_text_assembly()
	
	#test_patch()
	
	# EOF
