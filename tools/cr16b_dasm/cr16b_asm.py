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

OP_ADD = 0b0001	# adduw
OP_SUB = 0b1111	# subw
OP_CMP = 0b0111
OP_MOV = 0b1100	# movw

OP_PUSH = 0b0110
OP_POP = 0b0110	# Same as PUSH! But param differs
OP_POPRET = 0b0110	# Same as PUSH! But param differs

# List of basic 3-letter mnemonics that can be all handled the same way
OP_BASICS = {
	'mov': OP_MOV,
	'add': OP_ADD,
	'sub': OP_SUB,
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
	
	def dump(self):
		"""Output data store"""
		put(' '.join(['%02X'%b for b in self.stor.get_data()]))
	
	def clear(self):
		self.stor.clear()
	
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
				#@FIXME: Negative numbers!!
				if (w[:3] == '$0x'): params.append(int(w[1:], 16))
				elif (w[:1] == '$'): params.append(int(w[1:]))
				elif (w[:2] == '0x'): params.append(int(w,16))
				else: params.append(w)
				
				# Continue with next param
				p = p[o+1:]
			
			# Handle mnemonics
			#put('%s	%s' % (mnem, str(params)))
			
			if mnem == 'movd':	# movd is a special case
				self.assemble_movd(params[0], str_to_reg(params[1][1:-1].split(',')[1]))
			
			elif mnem[:3] in OP_BASICS:
				# Handle all "basic" mnemonics the same way
				
				op = OP_BASICS[mnem[:3]]
				
				#@FIXME: adduw VS. addw VS. addcw: b, cb, w, cw, uw
				form = mnem[3:]
				
				if form == 'b':
					i = I_BYTE
				elif form == 'w':
					#@FIXME: Difference between "w" and "uw"?!?!?
					i = I_WORD
				elif form == 'uw':	#@FIXME!!!!!!!!!!!!!!!!!!
					#@FIXME: Difference between "w" and "uw"?!?!?
					i = I_WORD
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
	
	#@TODO: beq0/1i
	#@TODO: bne0/1i
	
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
	
	def assemble_br(self, disp, cond=COND_EQ):
		"""Assemble a branch with condition with given displacement, automatically choses the instruction size.
			cond:
				1=NE
		"""
		if (disp < 0b1000000000):
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
		"""Assemble branch and link. lnk_pair: 0=r1,r0, 1=r2,r1, ... 13 = 0b1101 = ra,era (R13), 14=RA, 15=SP"""
		
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

if __name__ == '__main__':
	
	"""
	asm = CR16B_Assembler()
	
	# Test: 000682:	00 66 98 09	6600 0998	movd    $0x100998, (r1,r0)
	#asm.assemble_movd(imm21=0x100998, dest_pair=0b0000)
	# Test: 0004AC:	20 66 FA 09	6620 09FA	movd    $0x1009FA, (r2,r1)
	#asm.assemble_movd(imm21=0x1009FA, dest_pair=0b0001)
	# Test: 0004C6:	4C 66 00 00	664C 0000	movd    $0x1C0000, (r3,r2)
	#asm.assemble_movd(imm21=0x1C0000, dest_pair=0b0010)
	# Test: 000588:	80 66 0C 0B	6680 0B0C	movd    $0x100B0C, (r5,r4)
	#asm.assemble_movd(imm21=0x100B0C, dest_pair=0b0100)
	
	# Tests
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
	
	# Test: 00041A:	BA 6D      	6DBA     	popret  $2, era ; LMM
	#asm.assemble_popret(reg=REG_ERA, count=2)	# popret  $2, era ; LMM
	# Test: 000458:	EE 6C      	6CEE     	pop     $4, r7
	#asm.assemble_pop(reg=REG_R7, count=4)	# pop     $4, r7
	# Test: 000928:	96 6C      	6C96     	pop     $1, r11
	#asm.assemble_pop(reg=REG_R11, count=1)	# pop     $1, r11
	
	# Test: 001026:	DB 17      	17DB     	jump    (ra,era)
	#asm.assemble_jump(reg_pair=REG_ERA)	# jump    (ra,era)
	asm.dump()
	"""
	
	
	
	"""
	# Test different formats!
0020FA:	00 00      	0000     	addb    $0, r0
0027CE:	04 00      	0004     	addb    $0x4, r0

0027B4:	E8 13      	13E8     	addcb   $0x8, sp

0020A8:	01 20      	2001     	addw    $0x1, r0
0020AC:	61 20      	2061     	addw    $0x1, r3

0020AE:	80 32      	3280     	addcw   $0, r4
0020AA:	20 32      	3220     	addcw   $0, r1

002102:	F1 23 EE FF	23F1 FFEE	adduw   $-0x12, sp


0020B0:	A1 3E      	3EA1     	subw    $0x1, r5
0020B2:	C0 3A      	3AC0     	subcw   $0, r6
	"""
	
	
	
	'''
	# Assemble by manually calling each method
	asm = CR16B_Assembler()
	asm.pc = 0x200
	#asm.assemble_movw(0xb700, REG_SP)	# movw    $0xB700, sp
	asm.assemble_basic_imm_reg_medium(op=OP_MOV, i=I_WORD, imm16=0xb700, dest_reg=REG_SP)
	asm.assemble_push(reg=REG_R0, count=2)	# push    $2, r0
	asm.assemble_movd(0x189E91, REG_R4)	# movd    $0x189E91, (r5,r4)
	asm.assemble_movd(0x18AB57, REG_R2)	# movd    $0x18AB57, (r3,r2)
	asm.assemble_bal(0x1805c4)	# bal     (ra,era), 0x1805c4
	asm.assemble_basic_imm_reg_short(op=OP_ADD, i=I_WORD, imm5=4, dest_reg=REG_SP)	# adduw   $0x4, sp
	asm.assemble_basic_imm_reg_short(op=OP_CMP, i=I_BYTE, imm5=1, dest_reg=REG_R0)	# cmpb    $0x1, r0
	#asm.assemble_bne(disp=0x16)
	asm.assemble_br(cond=COND_NE, disp=0x16)
	asm.dump()
	'''
	
	
	
	'''
	# Assemble using a text listing
	asm2 = CR16B_Assembler(pc=0x200)
	asm2.assemble("""
		movw $0xb700, sp
		push $2, r0
		movd    $0x189E91, (r5,r4)	; 9E91 = "Achtung! Kassette beenden! (J/N)?"
		movd    $0x18AB57, (r3,r2)	; AB57 = "Schuetzt die Erde!"
		bal     (ra,era), 0x1805c4
		adduw   $0x4, sp
		cmpb    $0x1, r0
		bne     0x22c
	""")
	asm2.dump()
	'''
	
	
	### Patch a ROM
	filename_src = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update.dump.000.seg0-64KB__4KB_used.bin'
	filename_dst = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update_hacked.8KB.bin'
	
	# Create a copy
	copy_file(filename_src, filename_dst, ofs=0, size=8192)
	
	# Patch it
	text = """
		;movw $0xb700, sp
		
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
	
	
	# EOF
