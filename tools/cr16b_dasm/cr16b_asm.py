#!/usr/bin/python3
"""
Not-yet-Assembler for
National Semiconductor's CR16B CPU

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
def str_to_format(t):
	# Format (b/w)
	form = t[-1:]
	if form == 'b': i = I_BYTE
	elif form == 'w': i = I_WORD
	else:
		raise TypeError('Unknown format identifier "%s" in mnemonic "%s"!' % (form, t))
	return i


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
OP_MOVZ = 0b10101	# movzX - kinda special...

OP_PUSH = 0b0110
OP_POP = 0b0110	# Same as PUSH! But param differs
OP_POPRET = 0b0110	# Same as PUSH! But param differs

# List of basic 3-letter mnemonics that can be all handled the same way
OP_BASICS = {
	'mov': OP_MOV,
	'movz': OP_MOVZ,
	
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
	if (reg.startswith('(')):
		reg = reg[1:-1]
	
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
COND_CS = 0b0010
COND_CC = 0b0011
COND_HI = 0b0100
COND_LS = 0b0101
COND_GT = 0b0110
COND_LE = 0b0111
COND_FS = 0b1000
COND_FC = 0b1001
COND_LO = 0b1010
COND_HS = 0b1011
COND_LT = 0b1100
COND_GE = 0b1101
CONDS = {
	'eq': COND_EQ,
	'ne': COND_NE,
	'ge': COND_GE,
	'cs': COND_CS,
	'cc': COND_CC,
	'hi': COND_HI,
	'ls': COND_LS,
	'lo': COND_LO,
	'hs': COND_HS,
	'gt': COND_GT,
	'le': COND_LE,
	'fs': COND_FS,
	'fc': COND_FC,
	'lt': COND_LT,
}

def str_is_num(t):
	"""Check if the string is a parsable number"""
	if (t[:3] == '$0x'): return True
	elif (t[:4] == '$-0x'): return True
	elif (t[:1] == '$'): return True
	elif (t[:2] == '0x'): return True
	return t.isnumeric()

def str_to_num(t):
	if (t[:3] == '$0x'): return int(t[1:], 16)
	elif (t[:4] == '$-0x'): return 0x10000 - int(t[2:], 16)
	elif (t[:1] == '$'): return int(t[1:])
	elif (t[:2] == '0x'): return int(t,16)
	return int(t)

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
		else:
			self.pc = pc
		
		#pc_start = pc
		
		for line in text.split('\n'):
			#put('Parsing "%s"' % line)
			pc = self.pc	# So we can fiddle around more easily
			
			# Strip away comments
			if ';' in line: line = line[:line.index(';')]
			
			# Condense white space
			#@FIXME: Oh come on! Use a regexp or something!
			line = line.replace('\t', ' ')
			line = line.replace('    ', ' ')
			line = line.replace('  ', ' ')
			line = line.replace('  ', ' ')
			line = line.replace(', ', ',')
			line = line.strip()
			
			# Skip empty lines
			if line == '': continue
			
			# Remember labels
			if line[-1:] == ':':
				#put('Remembering label "%s" as pc=0x%06X...' % (mnem[:-1], self.pc))
				self.labels[line[:-1]] = pc
				continue
			
			# lower case from now on
			line = line.lower()
			
			# Parse mnemonic and parameters
			words = line.split(' ')
			mnem = words[0]
			
			
			# Parse remainder
			p = '' if len(words) < 2 else words[1]
			
			# Split parameters
			params = []
			while len(p) > 0:
				#put('"%s"' % p)
				# Find parameter delimiter
				try:
					#if p[:1] == '(':	# Handle nested commas, e.g. "(ra,era)" etc.
					if ('(' in p) and (p.index('(') < p.index(',')):	# Handle nested commas, e.g. "(ra,era)" etc.
						o = p.index(',', p.index(')'))
					else:
						o = p.index(',')
				except ValueError:
					o = len(p)
				
				# Get the first remaining word
				w = p[:o]
				
				# Handle immediates and addresses
				if ('(' in w) and (w.index('(') > 0):
					# Relative (e.g. "5(sp)")
					params.append((
						str_to_num(w[:w.index('(')]),
						w[w.index('('):]	#w[w.index('(')+1:-1]
					))
				elif (w[:3] == '$0x'): params.append(int(w[1:], 16))
				elif (w[:4] == '$-0x'): params.append(0x10000 - int(w[2:], 16))
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
			
			if mnem == 'nop':
				self.assemble_nop()
			
			# SBIT,CBIT, TBIT, STORi $imm4, X
			elif mnem in ('storb', 'loadb', 'storw', 'loadw'):
				
				#@TODO: Phew.... what a permutation mess!
				# load	disp(reg)	reg
				# load	addr	reg
				# stor	reg	disp(reg)
				# stor	reg	addr
				# stor	imm	disp(reg)
				# stor	imm	addr
				# ...each as byte and word variant
				# ...plus some special store with far addressing
				i = str_to_format(mnem)
				
				if mnem.startswith('load'):
					# LOAD
					if type(params[0]) is int:
						# LOAD abs, reg
						self.assemble_load(i=i,	src_reg=None, src_reg_is_far=None, src_disp=params[0], dest_reg=str_to_reg(params[1])	)
					else:
						# LOAD disp+reg, reg
						src_regs = params[0][1][1:-1].split(',')
						self.assemble_load(i=i,	src_reg=str_to_reg(src_regs[-1]), src_reg_is_far=(len(src_regs) > 1), src_disp=params[0][0], dest_reg=str_to_reg(params[1])	)
					
				else:
					# STOR
					if type(params[0]) is int:
						# STOR imm, ...
						if type(params[1]) is int:
							# STOR imm, abs
							self.assemble_stor(i=i,	src_reg=None, src_imm=params[0],	dest_reg=None, dest_disp=params[1]	)
						else:
							# STOR imm, disp+reg
							self.assemble_stor(i=i,	src_reg=None, src_imm=params[0],	dest_reg=str_to_reg(params[1][1]), dest_disp=params[1][0]	)
					else:
						# STOR reg, ...
						if type(params[1]) is int:
							# STOR reg, abs
							self.assemble_stor(i=i,	src_reg=str_to_reg(params[0]), src_imm=None,	dest_reg=None, dest_disp=params[1]	)
						else:
							# STOR reg, disp+reg
							self.assemble_stor(i=i,	src_reg=str_to_reg(params[0]), src_imm=None,	dest_reg=str_to_reg(params[1][1]), dest_disp=params[1][0]	)
				pass
			
			elif mnem == 'movd':	# movd is a special case, because it uses a register pair (see manual)
				self.assemble_movd(params[0], str_to_reg(params[1][1:-1].split(',')[1]))
				
			elif mnem == 'movzb':
				src_reg = str_to_reg(params[0])
				dest_reg = str_to_reg(params[1])
				self.assemble_basic_reg_reg(op=OP_MOVZ, i=I_BYTE, src_reg=src_reg, dest_reg=dest_reg, op2=0)
			
			elif mnem[:-1] in OP_BASICS:
				# Handle all "basic" mnemonics the same way
				
				op = OP_BASICS[mnem[:-1]]
				i = str_to_format(mnem)	# WORD/BYTE
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
				self.assemble_bal(disp21=params[1] - pc, lnk_pair=str_to_reg(params[0][1:-1].split(',')[1]))
			
			
			#elif mnem == 'beq0b':	self.assemble_brcond(cond=COND_EQ, val1=0, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			#elif mnem == 'beq1b':	self.assemble_brcond(cond=COND_EQ, val1=1, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			#elif mnem == 'bne0b':	self.assemble_brcond(cond=COND_NE, val1=0, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			#elif mnem == 'bne1b':	self.assemble_brcond(cond=COND_NE, val1=1, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			elif (len(mnem) == 5) and (mnem[:3] in ('beq', 'bne')):	# Special compare-and-branch (beq0/1b/2)
				self.assemble_brcond(
					cond=COND_NE if mnem[1:3] == 'ne' else COND_EQ,	# condition: eq or ne
					val1=int(mnem[3:4]),	# val: 0 or 1
					i=I_WORD if mnem[-1:] == 'w' else I_BYTE,	# format: b or w
					reg=str_to_reg(params[0]),	# register
					disp5m1=params[1] - pc	# displacement
				)
			
			elif (mnem[:1] == 'b') and (mnem[1:] in CONDS):	# beq, bne, ...
				self.assemble_br(disp=params[0] - pc, cond=CONDS[mnem[1:]])
			
			elif mnem == 'br':
				self.assemble_br(disp=params[0] - pc)	# cond=0x0e
			
			elif mnem == 'jump':
				self.assemble_jump(reg_pair=str_to_reg(params[0][1:-1].split(',')[1]))
			
			else:
				raise KeyError('Mnemonic "%s" not part of the *very* limited set of supported OpCodes!' % mnem)
			
		#
		
		return self.stor.get_bytes()
	
	def assemble_nop(self):
		self.w16(0x0200)
	
	def assemble_basic_reg_reg(self, op, i, src_reg, dest_reg, op2=1):
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
			| op2	# Usually 1
		
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
	
	
	def assemble_load(self, i, src_reg, src_reg_is_far, src_disp, dest_reg):
		"""src_size = 0 (5-bit small disp.)
		Since it is not clear for RR loads which size to use, it must be specified
		
		"""
		if (src_reg is None):
			# LOAD abs
			self.w32(
				  ((src_disp & 0b001111111111111111) << 16)\
				| (0b10 << 14)\
				| (i << 13)\
				| (0b11 << 11)\
				| (((src_disp & 0b110000000000000000) >> 16) << 9)\
				| (dest_reg << 5)\
				| 0b11111
			)
		elif (src_reg is not None) and (src_reg_is_far):
			# LOAD rr (medium/big)
			self.w32(
				  ((src_disp & 0b001111111111111111) << 16)\
				| (0b10 << 14)\
				| (i << 13)\
				| (0b11 << 11)\
				| (((src_disp & 0b110000000000000000) >> 16) << 9)\
				| (dest_reg << 5)\
				| (src_reg << 1)\
				| 0b1
			)
			
		elif (src_reg is not None) and (not src_reg_is_far) and (abs(src_disp) < 32):
			# LOAD rr (short 5-bit displacement)
			self.w16(
				  (0b10 << 14)\
				| (i << 13)\
				| (((src_disp & 0b11110) >> 1) << 9)\
				| (dest_reg << 5)\
				| (src_reg << 1)\
				| (src_disp & 0b1)
			)
			
		else:
			raise TypeError('Parameter combination not yet supported')
		
	def assemble_stor(self, i, src_reg, src_imm, dest_reg, dest_disp):
		
		#@TODO: STOR with register-relative and no displacement and 4-bit immediate
		#self.assemble_stor_rr(reg= , imm4=params[0])
		
		#@TODO: STOR with register-relative and 16-bit displacement and 4-bit immediate
		#self.assemble_stor_rr16(reg=..., disp16=... , imm4=params[0])
		
		#@TODO: STOR with absolute 18-bit address and 4-bit immediate
		#self.assemble_stor_abs(ad18=params[1], imm4=params[0])
		if (src_reg is not None) and (dest_reg is None):
			# Reg to Absolute
			self.w32(
				  ((dest_disp & 0b001111111111111111) << 16)\
				| (0b11 << 14)\
				| (i << 13)\
				| (0b11 << 11)\
				| (((dest_disp & 0b110000000000000000) >> 16) << 9)\
				| (src_reg << 5)\
				| 0b11111
			)
		elif (src_reg is None) and (dest_reg is None):
			# Imm4 to 18-bit absolute
			
			if src_imm < 16:
				self.w32(
					  ((dest_disp & 0b001111111111111111) << 16)\
					| (0b00 << 14)\
					| (i << 13)\
					| (0b0010 << 9)\
					| (((dest_disp & 0b100000000000000000) >> 17) << 8)\
					| (0b11 << 6)\
					| (((dest_disp & 0b010000000000000000) >> 16) << 5)\
					| (src_imm << 1)\
					| 0b0
				)
			else:
				raise ValueError('Immediate too big (4 bits only) for big absolute addressing')
				
		elif (src_reg is not None) and (dest_reg is not None) and (dest_disp is not None):
			# Reg to Reg-relative
			if abs(dest_disp) < 32:
				# Short displacement (5 bits)
				self.w16(
					  (0b11 << 14)\
					| (i << 13)\
					| (((dest_disp & 0b11110) >> 1) << 9)\
					| (src_reg << 5)\
					| (dest_reg << 1)\
					| (dest_disp & 0b1)
				)
			#elif abs(dest_disp) < (128*1024):
			#	# Medium displacement
			#	self.w32(
			else:
				raise ValueError('Larger register-relative displacements not yet supported')
		else:
			raise TypeError('Parameter combination not yet supported')
		
	
	def assemble_br(self, disp, cond=0x0e):
		"""Assemble a branch with condition with given displacement, automatically choses the instruction size.
			cond:
				1=NE
				
				0xe=no condition
		"""
		
		if disp < 0:
			# Backwards
			#@FIXME: This is done by trial and error
			self.assemble_br_medium(disp=disp + 0x200000, cond=cond)	#0x0e)
		elif (disp < 0b1000000000):
			#put('Short')
			self.assemble_br_short(disp=disp, cond=cond)
		else:
			#put('Long')
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
	
	def assemble_bal(self, disp21, lnk_pair=REG_ERA):
		"""Assemble branch and link for Large Memory Model.
		lnk_pair: 0=r1,r0, 1=r2,r1, ... 13 = 0b1101 = ra,era (R13), 14=RA, 15=SP"""
		
		#if pc is None: pc = self.pc
		#disp = dest - pc
		
		# BAL (ra, era) - CR16B Large Memory Format
		#	d15..d1 at 31..17
		#	d20 at 16
		#	const at 15..9	(0b0111011 for "bal")
		#	lnk-pair at 8..5	(0b1101 = 13 for "ra,era")
		#	d16 at 4
		#	d19..d17 at 1
		#             d:098765432109876543210
		instr32 = \
			  (((disp21 & 0b000001111111111111110) >> 1) << 17)\
			| (((disp21 & 0b100000000000000000000) >> 20) << 16)\
			| (0b0111011 << 9)\
			| (lnk_pair << 5)\
			| (((disp21 & 0b000010000000000000000) >> 16) << 4)\
			| (((disp21 & 0b011100000000000000000) >> 17) << 1)
		
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
	"""Helper to check assembly text against asserted binary output"""
	put('Checking "%06X	%s" =?= %s' % (pc, text, ' '.join([ '%02X' % b for b in bin]) ))
	
	asm = CR16B_Assembler()
	bin2 = asm.assemble(text, pc=pc)
	#asm.dump()
	
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
	# Test: 034420:	0F 78      	780F     	movw    r7, r0
	assert_assembly('movw    r7, r0', [0x0f, 0x78])
	# Test: 000004:	11 38 00 01	3811 0100	movw    $0x0100, r0
	assert_assembly('movw    $0x0100, r0', [0x11, 0x38, 0x00, 0x01])
	
	# Test: 034442:	02 6A      	6A02     	movzb   r1, r0
	assert_assembly('movzb   r1, r0', [0x02, 0x6a])
	# Test: 0360CA:	C0 6A      	6AC0     	movzb   r0, r6
	assert_assembly('movzb   r0, r6', [0xc0, 0x6a])
	
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
	
	# Test: 000460:	F1 23 E6 FF	23F1 FFE6	adduw   $-0x1A, sp
	assert_assembly('adduw   $-0x1A, sp', [0xf1, 0x23, 0xe6, 0xff])
	
	# Test: 002A2A:	02 1E      	1E02     	subb    $0x2, r0
	assert_assembly('subb    $0x2, r0', [0x02, 0x1E])
	# Test: 00204A:	A1 3E      	3EA1     	subw    $0x1, r5
	assert_assembly('subw    $0x1, r5', [0xA1, 0x3E])
	# Test: 00204C:	C0 3A      	3AC0     	subcw   $0, r6
	assert_assembly('subcw   $0, r6', [0xc0, 0x3a])
	
	
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
	#asm.assemble_brcond(cond=COND_EQ, val1=0, i=I_BYTE, reg=REG_R8, disp5m1=(0x031952 - 0x03194A))
	assert_assembly('beq0b   r8, 0x031952', [0x09, 0x15], pc=0x03194A)
	# Test: 031964:	49 15      	1549     	beq1b   r8, 0x03196C
	#asm.assemble_brcond(cond=COND_EQ, val1=1, i=I_BYTE, reg=REG_R8, disp5m1=(0x03196C - 0x031964))
	assert_assembly('beq1b   r8, 0x03196C', [0x49, 0x15], pc=0x031964)
	# Test: 015412:	8D 14      	148D     	bne0b   r0, 0x01541E	; back to loop
	#asm.assemble_brcond(cond=COND_NE, val1=0, i=I_BYTE, reg=REG_R0, disp5m1=(0x1541E - 0x015412))
	assert_assembly('bne0b   r0, 0x01541E	; back!', [0x8d, 0x14], pc=0x015412)
	# Test: 015904:	CB 14      	14CB     	bne1b   r0, 0x01590E
	#asm.assemble_brcond(cond=COND_NE, val1=1, i=I_BYTE, reg=REG_R0, disp5m1=(0x01590E - 0x015904))
	assert_assembly('bne1b   r0, 0x01590E', [0xcb, 0x14], pc=0x015904)
	#Test: 002256:	89 34      	3489     	bne0w   r0, 0x00225E
	assert_assembly('bne0w   r0, 0x00225E', [0x89, 0x34], pc=0x002256)
	
	# Test: 0014D2:	20 2E      	2E20     	cmpw    $0, r1
	assert_assembly('cmpw    $0, r1', [0x20, 0x2e], pc=0x0014D2)
	# Test: 0014D4:	D2 40      	40D2     	bgt     0x0014E6
	assert_assembly('bgt     0x0014E6', [0xd2, 0x40], pc=0x0014D4)
	# Test: 0014D6:	26 40      	4026     	bne     0x0014DC
	assert_assembly('bne     0x0014DC', [0x26, 0x40], pc=0x0014D6)
	
	#@FIXME: Wrong output!
	#### Test: 0014E4:	F8 5E      	5EF8     	ble     0x0014EC
	###assert_assembly('ble     0x0014EC', [0xf8, 0x5e], pc=0x0014E4)
	
	# Test: 001720:	EA 40      	40EA     	ble     0x00172A
	assert_assembly('ble     0x00172A', [0xea, 0x40], pc=0x001720)
	
	# Test: 0014EA:	80 42      	4280     	bhi     0x00150A
	assert_assembly('bhi     0x00150A', [0x80, 0x42], pc=0x0014EA)
	# Test: 0014F0:	3A 41      	413A     	bfc     0x00150A
	assert_assembly('bfc     0x00150A', [0x3a, 0x41], pc=0x0014F0)
	
	#asm.dump()
	put('All tests OK')


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

def test_text_parser():
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

def run_patch():
	"""Patch a ROM"""
	filename_src = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update.dump.000.seg0-64KB__4KB_used.bin'
	filename_dst = '/z/data/_code/_c/V-Tech/vcxdk.git/__VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GL8008CX_Update_hacked.8KB.bin'
	
	# Create a copy
	copy_file(filename_src, filename_dst, ofs=0, size=8192)
	
	'''
	# Patch it
	ofs = 0x100
	bin = asm.assemble(pc=ofs, text="""
	
	""")
	
	put('Patching at offset 0x%06X (%d bytes)...' % (ofs, len(bin)))
	patch_file(filename_dst, ofs=ofs, data=bin)
	'''
	
	'''
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
	'''
	
	
	# Patch all potential entry points
	ofss = [
		0x000200,
		#		0x000400,
		#	0x00041C,
		#		0x000476,	#0x00045C,
		#0x00051C,	# This offset on its own is enough to be called (but freezes with half-lit LEDs...)
		#	0x000542
	]
	
	text = """
		push    $2, era
		
		; Delay
		movw    $0x7800, r0
	delay_loop:
		subw    $1, r0
		cmpw    $0, r0
		bne     :delay_loop
		
		
		; Try showing a prompt
		movd    $0x034191, (r1,r0)	; Dunny what this param does...
		push    $2, r0
		;movd    $0x189E91, (r5,r4)	; 9E91 = "Achtung! Kassette beenden! (J/N)?"
		movd    $0x18AB57, (r3,r2)	; AB57 = "Schuetzt die Erde!"
		
		movd    $0x100B18, (r5,r4)	; 00B18 = STRING "028100"
		;movd    $0x100AD2, (r3,r2)	; 00AD2 = STRING "Update Programm-Zusatzkassette"
		
		bal     (ra,era), 0x1805C4	; prompt_yesno__title_r3r2__text_r5r4__sys5c4
		adduw   $0x4, sp
		
		
		; Delay2
		movw    $0x7800, r0
	delay2_loop:
		subw    $1, r0
		cmpw    $0, r0
		bne     :delay2_loop
		
		
		; Try showing a info popup
		movd    $0x034191, (r1,r0)
		adduw   $-0x8, sp
		storw   r0, 0x4(sp)
		storw   r1, 0x6(sp)
		
		movd    $0x18AB57, (r1,r0)	; AB57 = "Schuetzt die Erde!"
		storw   r0, 0(sp)
		storw   r1, 0x2(sp)
		
		movb    $0, r4
		movd    $0x084D40, (r3,r2)
		bal     (ra,era), 0x018CC4	;0x018CC4	; show_info_popup_r1r0
		adduw   $0x8, sp
		
		
		; Exit/Reboot
		;popret  $2, era
		;pop  $2, era
		;jump    (ra,era)
		bal     (ra,era), 0x180000	; Reboot
	
	halt_loop:
		br      :halt_loop
		
	"""
	
	for ofs in ofss:
		asm = CR16B_Assembler()
		bin = asm.assemble(pc=ofs, text=text)
		asm.dump()
		
		put('Patching at offset 0x%06X (%d bytes)...' % (ofs, len(bin)))
		patch_file(filename_dst, ofs=ofs, data=bin)
	


if __name__ == '__main__':
	
	
	#test_manual_assembly()
	#test_text_parser()
	test_instructions()
	
	#run_patch()
	
	# EOF
