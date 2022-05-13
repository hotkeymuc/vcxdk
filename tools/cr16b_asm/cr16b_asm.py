#!/usr/bin/python3
"""
Not-yet-Assembler for
National Semiconductor's CR16B CPU

(at least a tool for helping me patch some bytes in the ROM)


TODO:
	* Larger register-displacements are not yet implemented, e.g. "36(sp)" (> 32)
	* Some specials are missing, e.g. wait, res, mulXX, storm, loadm, eiwait, ei, di, ...
	* There are no real "sections", yet - only code or RAM
	* Symbol resolution is dirty! They should get resolved when actually acting upon them, not at line-parse time

2022-04-20 Bernhard "HotKey" Slawik
"""

def put(t):
	print(t)
def put_debug(t):
	#pass
	print(t)

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
OP_ADD  = 0b00000	# addX
OP_ADDU = 0b00001	# adduX
OP_ADDC = 0b01001	# addcX
OP_SUB  = 0b01111	# subX
OP_SUBU = 0b00110	# subuX
OP_SUBC = 0b01101	# subcX
OP_CMP  = 0b00111
OP_MOV  = 0b01100	# movX
OP_MOVX = 0b10100	# movxX
OP_MOVZ = 0b10101	# movzX - kinda special...

OP_AND = 0b11000
OP_OR  = 0b01110
OP_XOR = 0b00110
OP_LSH = 0b00101
OP_ASHU = 0b00100	# ashuX

OP_MUL = 0b00011
#OP_MULS = 0b00011

OP_PUSH = 0b0110
OP_POP  = 0b0110	# Same as PUSH! But param differs
OP_POPRET = 0b0110	# Same as PUSH! But param differs

# List of basic 3-letter mnemonics that can be all handled the same way
OP_BASICS = {
	'mov' : OP_MOV,
	#'movx': OP_MOVX,
	'movz': OP_MOVZ,
	
	'add' : OP_ADD,
	'addu': OP_ADDU,
	'addc': OP_ADDC,
	
	'sub' : OP_SUB,
	'subu': OP_SUBU,
	'subc': OP_SUBC,
	
	'mul' : OP_MUL,
	#'muls': OP_MULS,
	
	'cmp' : OP_CMP,
	
	'and' : OP_AND,
	'or'  : OP_OR,
	'xor' : OP_XOR,
	
	'lsh' : OP_LSH,
	'ashu' : OP_ASHU,
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
	if   (t[:3] == '$0x'): return True
	elif (t[:4] == '$-0x'): return True
	elif (t[:2] == '$-') and (t[2:].isnumeric()): return True
	elif (t[:1] == '$') and (t[1:].isnumeric()): return True
	elif (t[:1] == '-') and (t[1:].isnumeric()): return True
	elif (t[:2] == '0x'): return True
	return t.isnumeric()

def str_to_num(t):
	if   (t[:3] == '$0x'): return int(t[1:], 16)
	elif (t[:4] == '$-0x'): return -int(t[2:], 16)	#0x10000 - int(t[2:], 16)
	elif (t[:1] == '$'): return int(t[1:])
	elif (t[:1] == '-'): return -int(t[1:])
	elif (t[:2] == '0x'): return int(t,16)
	return int(t)





RAM_START = 0xb700	# Default start for all data inside a non-text section
ROM_SECTIONS = ['text', '.rdata_2', '.frdat_2']	# Order in which to put the ROM sections into file
SECTION_OFFSETS = {
	'text': 0x000000,
	'.rdata_2': 0x000000,
	'.frdat_2': 0x000000,
	'.bss_2': RAM_START,
}


class DataStore:
	def __init__(self):
		self.data = []
		self.ofs = 0
	
	def clear(self):
		self.data = []
		self.ofs = 0
	
	def w8(self, v8):
		self.data.append(v8)
		self.ofs += 1
	
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


class Section:
	"""One section, like text, bss2, rdata_2, ..."""
	
	def __init__(self, name, address=0x000000):
		self.name = name
		self.store = DataStore()
		self.address = address
		self.labels = {}
	
	def clear(self):
		self.store.clear()
		
	def get_ofs(self):
		return self.store.ofs
	
	def get_address(self):
		return self.address + self.get_ofs()
		
	def register_label(self, name):
		"""Remember current offset as named label"""
		self.labels[name] = self.get_ofs()
	
	def has_label(self, name):
		return name in self.labels
	
	def get_label_address(self, name):
		return self.address + self.labels[name]



class CR16B_Assembler:
	"""The assembler"""
	def __init__(self):
		#self.stor = DataStore()
		#self.pc = 0
		self.align = 2
		
		#self.labels = {}
		self.constants = {}
		self.sections = {}
		
		s = Section('text', address=0x000000)
		self.sections['text'] = s
		self.section = s
	
	def put(self, t):
		put(t)
	
	def put_debug(self, t):
		put_debug(t)
	
	def enter_section(self, name):
		if name in self.sections:
			section = self.sections[name]
		else:
			address = SECTION_OFFSETS[name] if name in SECTION_OFFSETS else 0
			self.put('New section "%s" at 0x%06X!' % (name, address))
			self.sections[name] = Section(name, address=address)
		
		#self.put_debug('Entering section "%s"...' % name)
		self.section = self.sections[name]
	
	def register_label(self, name):
		if self.section.has_label(name):
			self.put_debug('Current section "%s" already has label "%s"' % (self.section.name, name))
		
		self.section.register_label(name)
	
	def has_label(self, name):
		for k,section in self.sections.items():
			if section.has_label(name):
				return True
		return False
	
	def get_label_address(self, name):
		for k,section in self.sections.items():
			if section.has_label(name):
				return section.get_label_address(name)
		
		#self.put('Label "%s" not found in any section (yet).' % name)
		return None
	
	def w_raw(self, v):
		if type(v) is list:
			for w in v:
				self.w8(w)
		else:
			self.w8(v)
	def w8(self, v8):
		self.section.store.w8(v8)
		#self.pc += 1
	def w16(self, v16):
		self.section.store.w16(v16)
		#self.pc += 2
	def w32(self, v32):
		self.section.store.w32(v32)
		#self.pc += 4
	def pad(self, num):
		for i in range(num):
			self.w8(0x00)
	def pad_to_alignment(self, a=None):
		"""Pad to given alignment"""
		al = self.align if a is None else a
		if (self.section.get_ofs() % al) != 0:
			put_debug('Padding...')
			while (self.section.get_ofs() % al) != 0:
				self.w8(0x00)
	
	
	def get_bytes(self):
		#return self.stor.get_data()
		#return [ s.store.get_data() for k,s in self.sections.items() ]
		bin = b''
		for name in ROM_SECTIONS:
			if not name in self.sections: continue
			self.put_debug('Concatenating ROM section "%s"...' % name)
			bin = bin + self.sections[name].store.get_bytes()
		return bin
	
	def dump(self):
		"""Output data store"""
		put(' '.join(['%02X'%b for b in self.get_bytes()]))
	
	
	def clear(self, keep_labels=False):
		for k,section in self.sections.items():
			section.store.clear()
		
		self.section = self.sections['text']
		
		if keep_labels:
			pass
		else:
			#self.labels = {}
			self.constants = {}
	
	def assemble(self, text, pc=None):
		"""Parse the given assembly text into a binary blob.
		This is a wrapper around the internal _assemble() method, so we can automatically initiate a multi-pass (for forward jumps).
		Since the compact binary format has different sized instructions for a branch, the binary size and label offsets may change depending on how far a label is away.
		This means: The output does not necessarily converge after 2 passes.
		"""
		
		# Assemble until all labels are resolved, branch distances have settled and the output "converges"
		MAX_PASS_NUM = 99
		pass_num = 0
		bin = None
		while (pass_num < MAX_PASS_NUM):
			pass_num += 1
			self.put('Pass #%d...' % pass_num)
			bin_old = bin
			bin, unresolved = self._assemble(text=text, pc=pc)
			
			#put('Sections: %s' % str(self.sections))
			#put('Constants: %s' % str(self.constants))
			
			#self.put('Relocating ROM sections...')
			relocated = False
			old_section = asm.sections[ROM_SECTIONS[0]]
			for name in ROM_SECTIONS[1:]:	# Only ROM sections / constants
				if not name in asm.sections: continue
				section = asm.sections[name]
				
				# Pad previous section to alignment
				if (old_section.get_ofs() % self.align > 0):
					self.put('Padding ROM section "%s" for relocation...' % old_section.name)
					while (old_section.get_ofs() % self.align > 0):
						old_section.w8(0x00)
				
				# Put new section after previous one
				address = old_section.address + old_section.get_ofs()
				if (address != section.address):
					self.put('Relocated ROM section "%s" after "%s" to address 0x%06X' % (section.name, old_section.name, address))
					section.address = address
					relocated = True
				
				# Continue
				old_section = section
			
			# Check if the binary has changed (i.e. another forward-label has been resolved)
			#self.put_debug(' '.join(['%02X'%b for b in bin]))
			
			if (bin == bin_old) and (not relocated):
				self.put('Output converged after %d(-1) passes.' % pass_num)
				
				if len(unresolved) > 0:
					raise NameError('Finished, but there are unresolvable identifiers left: %s' % str(unresolved))
				
				#put('Sections: %s' % str(self.sections))
				#put('Constants: %s' % str(self.constants))
				break
			
			self.put_debug('Output is still changing/relocating. Need to do another pass to verify')
			# Clear the output, but keep the labels
			self.clear(keep_labels=True)
		
		if pass_num >= MAX_PASS_NUM:
			raise RuntimeError('Too many passes! (%d)' % pass_num)
		
		return bin
	
	
	def _assemble(self, text, pc=None):
		"""Dirty assembly text parser"""
		
		#if pc is None:
		#	pc = self.pc
		#else:
		#	self.pc = pc
		if (pc is not None) and (pc != self.section.get_address()):
			# While testing BRANCH instructions, it is crucial to force a specific value for PC to check displacement encoding
			# But better shout out what's going on, because it might lead to bad bugs if it happens unnoticed.
			self.put('Forcing address of section "%s" from 0x%06X to 0x%06X' % (self.section.name, self.section.get_address(), pc))
			self.section.address += pc - self.section.get_address()
		
		unresolved = []	#0
		#pc_start = pc
		
		line_num = 0
		for line in text.split('\n'):
			line_num += 1
			#pc = self.pc	# So we can fiddle around more easily
			#self.put_debug('Parsing raw input: %06X	%s' % (pc, line))
			pc = self.section.get_address()
			
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
			
			self.put_debug('Parsing:	%06X	%s' % (pc, line))
			
			# Skip full-line comments
			if line[:1] == '#': continue
			
			# Remember labels and continue
			# (These might start with ".", so check this case first. Or else they might get ignored as "ignored directive")
			if line[-1:] == ':':
				label_name = line[:-1]
				
				"""
				old_label_address = self.get_label_address(label_name)
				new_label_address = self.section.get_address()
				
				if old_label_address is None:
					# Not yet known
					self.put('Remembering new label "%s"...' % label_name)
				else:
					# Label already known
					
					if old_label_address != new_label_address:
						self.put('Label "%s" is already known, but changed from 0x%06X to 0x%06X...' % (label_name, old_label_address, new_label_address))
						
					else:
						#self.put('Label "%s" is already known and steady at 0x%06X...' % (label_name, old_label_address))
						continue
				"""
				self.register_label(label_name)
				continue
			
			
			# Parse mnemonic and parameters
			words = line.split(' ')
			mnem = words[0].lower()
			
			
			# Some "." directives
			if mnem in ['.file', '.code_label', '.globl']:
				#self.put_debug('Ignoring directive "%s"' % mnem)
				continue
			
			elif mnem == '.section':
				section_name = words[1].split(',')[0]	#params[0]
				
				#self.put_debug('Changing to section "%s"...' % section_name)
				self.enter_section(section_name)
				continue
				
			elif mnem == '.text':
				
				#self.put_debug('Changing to section TEXT')
				self.enter_section('text')
				continue
				
			elif mnem == '.space':
				#@TODO: Reserver space in current section
				self.put_debug('Reserve %d bytes in section' % int(words[1]))
				self.pad(int(words[1]))
				continue
			
			
			# Parse remainder
			p = '' if len(words) < 2 else line[len(words[0])+1:]	#words[1]
			
			# Split parameters
			params = []
			while len(p) > 0:
				#self.put_debug('"%s"' % p)
				
				# Find parameter delimiter
				if p[:1] in ['"', "'"]:
					# String parameter - search for the end of it
					o = p.index(p[:1], 1)+1
					
					if ',' in p[o:]:
						o = p.index(',', o)
				else:
					try:
						# Handle nested commas, e.g. in register pairs like "(ra,era)" etc.
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
					# Register-relatives, e.g. "5(sp)"
					# Add them as a tuple
					params.append((
						str_to_num(w[:w.index('(')]),
						w[w.index('('):]	#w[w.index('(')+1:-1]
					))
				elif str_is_num(w): params.append(str_to_num(w))
				#elif (w[:3] == '$0x'): params.append(int(w[1:], 16))
				#elif (w[:4] == '$-0x'): params.append(- int(w[2:], 16))
				#elif (w[:1] == '$'): params.append(int(w[1:]))
				#elif (w[:2] == '0x'): params.append(int(w,16))
				#elif (w[:1] == ':'):
				#	label_name = w[1:]
				elif (w[:1] in ['.', '_', '$']):	# Assume ".foo" and "_bar" to be a defined symbols
					
					if w[:1] == '$': w = w[1:]
					#@FIXME: Better resolve labels later when accessing them, not before
					#@FIXME: Some mnemonics INTRODUCE a new identifier. Let them handle it and don't force-introduce dummy values!
					
					label_name = w
					if label_name in self.constants:
						label_addr = self.constants[label_name]
						#self.put_debug('Label "%s" resolved to 0x%06X' % (label_name, label_addr))
					elif self.has_label(label_name):
						label_addr = self.get_label_address(label_name)
					else:
						#label_addr = 0x1fffff	# Assume far address
						label_addr = pc + 0x10	# Assume short branch
						self.put_debug('(Yet) unknown label "%s" at line #%d, pc=0x%06X. Using dummy 0x%06X' % (label_name, line_num, pc, label_addr))
						
						unresolved.append(label_name)
					
					params.append(label_addr)
				
				elif (w[:1] == '$') and (w[1:] in self.labels):	# Accept "$.something"
					params.append(self.labels[w[1:]])
				elif w in self.constants:	# Accept ANY previously defined label
					params.append(self.constants[w])
				else:
					# Remember "as-is"
					params.append(w)
				
				# Continue with next param
				p = p[o+1:]
			
			# Handle mnemonics
			#self.put_debug('Handling:	%s	%s' % (mnem, str(params)))
			
			# Some non-CPU directives
			
			# Some of my own directives
			
			if mnem in ['db', '.ascii']:
				# Define byte(s)
				for p in params:
					if type(p) is int:
						self.w8(p)
					elif (type(p) is str) and (p[:1] == p[-1:]) and (p[:1] in ("'", '"')):
						is_esc = False
						
						p = p.replace('\\15', '\\r')	# "\r" is encoded as "\15". Uargh...
						p = p.replace('\\12', '\\n')	# "\n" is encoded as "\12". Uargh...
						
						for b in p[1:-1]:
							if b == '\\':
								is_esc = True
								continue
							if is_esc:
								if b == '0': b = chr(0)
								elif b == 'n': b = chr(12)
								elif b == 'r': b = chr(10)
								else: raise ValueError('Unknown escape in string: %s' % str(b))
								is_esc = False
							
							self.w8(ord(b))
					else:
						self.put('Unknown parameter to db/ascii: "%s"?' % str(p))
				#self.pad_to_alignment()
			elif mnem == '.align':
				# Pad code
				self.pad_to_alignment(params[0])
			elif mnem == '.word':
				self.w16((0x10000 + params[0]) % 0x10000)
			elif mnem == '.byte':
				self.w8((0x10000 + params[0]) % 0x100)
				#self.pad_to_alignment()
			elif mnem == '.set':
				label_name, label_value = words[1].split(',')
				self.constants[label_name] = int(label_value)
			
			#elif mnem == '.globl':
			#	label_name = words[1]
			#	#self.put_debug('Remembering .globl "%s" as 0x%06X' % (label_name, pc))
			#	self.labels[label_name] = pc
			
			elif mnem == 'ofs':
				# Pad until given address
				d = params[0] - pc
				if d < 0:
					raise ValueError('Invalid offset! We are already beyond the given address (0x%06X > 0x%06X)!' % (pc, params[0]))
				else:
					self.put_debug('Padding %d bytes until offset 0x%06X...' % (d, params[0]))
					self.pad(d)
				
			elif (len(words) > 1) and (words[1] == 'equ'):
				# Define EQU constants
				#self.labels[words[0]] = params[2]
				self.constants[label_name] = int(label_value)
				
			
			# CR16B instructions
			elif mnem == 'nop':
				self.assemble_nop()
			elif mnem == 'di':
				self.w16(0x7dde)
			elif mnem == 'ei':
				self.w16(0x7dfe)
			elif mnem == 'wait':
				self.w16(0x7ffe)
			
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
				i = str_to_format(mnem)	# byte or word
				
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
				
			elif mnem == 'movxb':
				src_reg = str_to_reg(params[0])
				dest_reg = str_to_reg(params[1])
				self.assemble_basic_reg_reg(op=OP_MOVX, i=I_BYTE, src_reg=src_reg, dest_reg=dest_reg, op2=0)
			
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
				#@TODO Make sure params[1] is a valid number
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
		
		return self.get_bytes(), unresolved
	
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
		#self.put_debug('imm=%d' % imm)
		if (imm == -16) or (imm >= -14 and imm <= 15):
			if imm < 0: imm = 0x20 + imm
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
			
		elif (src_reg is not None) and (not src_reg_is_far) and (src_disp is not None):
			if (abs(src_disp) < 32):
				# LOAD rr (short 5-bit displacement)
				self.w16(
					  (0b10 << 14)\
					| (i << 13)\
					| (((src_disp & 0b11110) >> 1) << 9)\
					| (dest_reg << 5)\
					| (src_reg << 1)\
					| (src_disp & 0b1)
				)
			elif abs(src_disp) < (2 << 18):
				# Medium displacement
				self.w32(
					  ((src_disp & 0b001111111111111111) << 16)\
					| (0b10 << 14)\
					| (i << 13)\
					| (0b10 << 11)\
					| (((src_disp & 0b110000000000000000) >> 16) << 9)\
					| (dest_reg << 5)\
					| (src_reg << 1)\
					| (0b1)
				)
			else:
				raise ValueError('Large register-relative LOAD displacements are not yet supported, sorry!')
			
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
			elif abs(dest_disp) < (2 << 18):
				# Medium displacement
				self.w32(
					  ((dest_disp & 0b001111111111111111) << 16)\
					| (0b11 << 14)\
					| (i << 13)\
					| (0b10 << 11)\
					| (((dest_disp & 0b110000000000000000) >> 16) << 9)\
					| (src_reg << 5)\
					| (dest_reg << 1)\
					| (0b1)
				)
			else:
				raise ValueError('Large register-relative STOR displacements are not yet supported, sorry!')
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
			#self.put_debug('Short')
			self.assemble_br_short(disp=disp, cond=cond)
		else:
			#self.put_debug('Long')
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
	"""Helper function to check assembly text against asserted binary output"""
	put('Checking "%06X	%s" =?= %s' % (pc, text, ' '.join([ '%02X' % b for b in bin]) ))
	
	asm = CR16B_Assembler()
	#bin2 = asm.assemble(text, pc=pc)
	asm._assemble(text, pc=pc)	# Only single pass needed
	
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
	
	
	import sys
	
	
	if len(sys.argv) < 2:
		put('No argument given, running test(s)...')
		
		# Enable what to do, e.g. do assembler self-tests or actually try assembling and patching something
		#test_manual_assembly()
		#test_text_parser()
		test_instructions()
		
		#run_patch()
		
		sys.exit()
	
	
	"""
	import getopt
	short_options = "c:s:hv"
	long_options  = ["config=", "suggestions=", "help", "version"]
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], short_options, long_options)
	except getopt.GetoptError, err:
		print str(err)
		sys.exit(1)
	"""
	
	import argparse
	argp = argparse.ArgumentParser(description='Compile CR16B assembly')
	
	# Add the arguments
	#argp.add_argument('--input', nargs='+', action='append', type=str, required=True, help='input file(s)')
	argp.add_argument('--pad', '-p', action='store', type=int, help='Pad output to given size')
	argp.add_argument('--stats', '-s', action='store_true', help='Show sections/constants after assembly')
	argp.add_argument('--verbose', '-v', action='count', default=0, help='Verbose output')
	argp.add_argument('--output', '-o', nargs='?', action='store', type=str, help='Output file')
	argp.add_argument(dest='input', nargs='+', action='append', type=str, help='Input file(s)')
	
	# Execute the parse_args() method
	args = argp.parse_args()
	
	input_filenames = args.input[0]
	output_filename = args.output
	pad = args.pad
	verbose = args.verbose
	
	if verbose == 0:
		# Disable put_debug()
		put_debug = lambda t: t
	
	ofs = 0
	text = ''
	for input_filename in input_filenames:
		put('Loading input file "%s"...' % input_filename)
		with open(input_filename, 'r') as h:
			text += h.read() + '\n\n'
	
	put('Assembling...')
	asm = CR16B_Assembler()
	asm.assemble(pc=ofs, text=text)
	
	if args.stats:
		put('Constants:')
		for k,c in asm.constants.items():
			put('\t* %s: 0x%06X / %d' % (k, c, c))
		
		put('Sections:')
		for k,section in asm.sections.items():
			put('\t* %s at 0x%06X: %s' % (section.name, section.address, ' '.join(['%02X'%b for b in section.store.get_data()])) )
		
	
	if output_filename is None:
		put('Dumping (stdout)...')
		asm.dump()
		#put(' '.join(['%02X'%b for b in bin]))
	else:
		bin = asm.get_bytes()
		
		put('Writing output file "%s"...' % output_filename)
		with open(output_filename, 'wb') as h:
			h.write(bin)
			if pad is not None:
				l = pad - len(bin)
				put_debug('Padding %d bytes to fill up %d bytes' % (l, pad))
				h.write(bytes([0] * l))
	
	
	# EOF
