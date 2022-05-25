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

OP_AND = 0b01000
OP_OR  = 0b01110
OP_XOR = 0b00110
OP_LSH = 0b00101
OP_ASHU = 0b00100	# ashuX

OP_MUL = 0b00011
OP_MULS = 0b00011

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
	'muls': OP_MULS,
	
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
	elif (t[:3] == '-0x'): return True
	elif (t[:1] == '-') and (t[1:].isnumeric()): return True
	elif (t[:2] == '0x'): return True
	return t.isnumeric()

def str_to_num(t):
	if   (t[:3] == '$0x'): return int(t[1:], 16)
	elif (t[:4] == '$-0x'): return -int(t[2:], 16)	#0x10000 - int(t[2:], 16)
	elif (t[:1] == '$'): return int(t[1:])
	elif (t[:3] == '-0x'): return -int(t[1:], 16)
	elif (t[:1] == '-'): return -int(t[1:])
	elif (t[:2] == '0x'): return int(t,16)
	return int(t)




from collections import OrderedDict

ROM_BASE_OFFSET = 0x0000	#0x100000
RAM_START = 0xb700	# Default start for all data inside a non-text section

# Order in which to put the ROM sections into file
ROM_SECTIONS = [
	'.text',
	
	'.rdata',	# read-only data
	'.rdata_1',
	'.rdata_2',
	
	'.frdat',	# read-only far data
	'.frdat_1',
	'.frdat_2'
	
]
RAM_SECTIONS = [
	'.data',	# initialized data
	'.data_1',
	'.data_2',
	
	'.bss',	# uninitialized data
	'.bss_1',
	'.bss_2',
	
	'.fdata',	# initialized far data
	
	'.fbss',	# uninitialized far data
	'.fbss_1',
	'.fbss_2'
]

SECTION_DEFAULT_OFFSETS = {
	'.text': 0x000000,	# program code
	'.rdata': 0x000000,	# read-only data
	'.rdata_1': 0x000000,
	'.rdata_2': 0x000000,
	
	'.data': 0x000000,	# initialized data
	'.data_1': 0x000000,
	'.data_2': 0x000000,
	
	'.bss': 0x000000,	# uninitialized data
	'.bss_1': 0x000000,	#RAM_START,
	'.bss_2': 0x000000,	#RAM_START,
	
	'.frdat': 0x000000,	# read-only far data
	'.frdat_1': 0x000000,
	'.frdat_2': 0x000000,
	
	'.fdata': 0x000000,	# initialized far data
	
	'.fbss': 0x000000,	# uninitialized far data
	'.fbss_1': 0x000000,	#RAM_START,
	'.fbss_2': 0x000000,	#RAM_START,
}

SECTION_BASE_OFFSETS = {
	'.text': 0x000000,
	'.rdata': ROM_BASE_OFFSET,
	'.rdata_1': ROM_BASE_OFFSET,
	'.rdata_2': ROM_BASE_OFFSET,
	'.frdat': ROM_BASE_OFFSET,
	'.frdat_1': ROM_BASE_OFFSET,
	'.frdat_2': ROM_BASE_OFFSET,
	
	'.data': RAM_START,
	'.data_1': RAM_START,
	'.data_2': RAM_START,
	'.fdata': RAM_START,
	
	'.bss': RAM_START,
	'.bss_1': RAM_START,
	'.bss_2': RAM_START,
	'.fbss': RAM_START,
	'.fbss_1': RAM_START,
	'.fbss_2': RAM_START,
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
	
	def __init__(self, name, base_address=0x000000):
		self.name = name
		self.store = DataStore()
		self.base_address = base_address	# This is the static offset added to accesses to this section (e.g. 0x100000 for CARTRIDGE ROM)
		self.relocation_offset = 0	# This is the relocation offset (used to relocate several sections together)
		self.labels = {}
	
	def clear(self):
		self.store.clear()
		
	def get_ofs(self):
		return self.store.ofs
	
	def get_address(self):
		return self.base_address + self.relocation_offset + self.get_ofs()
		
	def register_label(self, name):
		"""Remember current offset as named label"""
		self.labels[name] = self.get_ofs()
	
	def has_label(self, name):
		return name in self.labels
	
	def get_label_address(self, name):
		return self.base_address + self.relocation_offset + self.labels[name]



class CR16B_Assembler:
	"""The assembler"""
	def __init__(self):
		#self.stor = DataStore()
		#self.pc = 0
		self.align = 2
		
		#self.labels = {}
		self.constants = {}
		self.sections = {}
		
		s = Section('.text')
		self.sections['.text'] = s
		self.section = s
	
	def put(self, t):
		put(t)
	
	def put_debug(self, t):
		put_debug(t)
	
	def enter_section(self, name):
		if name in self.sections:
			section = self.sections[name]
		else:
			#address = SECTION_DEFAULT_OFFSETS[name] if name in SECTION_DEFAULT_OFFSETS else 0x000000
			#self.put('New section "%s" at 0x%06X!' % (name, address))
			#self.sections[name] = Section(name, address=address)
			base_address = SECTION_BASE_OFFSETS[name] if name in SECTION_BASE_OFFSETS else 0x000000
			self.put_debug('New section "%s" at 0x%06X!' % (name, base_address))
			self.sections[name] = Section(name, base_address=base_address)
		
		#self.put_debug('Entering section "%s"...' % name)
		self.section = self.sections[name]
	
	def register_label(self, name):
		if self.section.has_label(name):
			self.put_debug('Current section "%s" already knows label "%s"' % (self.section.name, name))
		
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
		"""Returns the concatenated ROM section bytes"""
		#return self.stor.get_data()
		#return [ s.store.get_data() for k,s in self.sections.items() ]
		bin = b''
		for name in ROM_SECTIONS:
			if not name in self.sections: continue
			#self.put_debug('Concatenating ROM section "%s"...' % name)
			bin = bin + self.sections[name].store.get_bytes()
		return bin
	
	def dump(self):
		"""Output data store"""
		put(' '.join(['%02X'%b for b in self.get_bytes()]))
	
	
	def clear(self, keep_labels=False):
		for k,section in self.sections.items():
			section.store.clear()
		
		self.section = self.sections['.text']
		
		if keep_labels:
			pass
		else:
			#self.labels = {}
			self.constants = {}
	
	def relocate(self, section_names):
		"""Relocate the sections according to order given as parameter (name list)"""
		
		if len(section_names) == 0:
			return False
		
		relocated = False
		
		# Search first available section
		#old_section = asm.sections[section_names[0]]
		old_section = None
		for name in section_names:
			if name in asm.sections:
				old_section = asm.sections[name]
				break
		if old_section is None:
			#put('Could not find a starting section!')
			return False
		
		for name in section_names:	# Only given sections
			if not name in asm.sections: continue
			section = asm.sections[name]
			if section == old_section: continue
			
			# Pad previous section to alignment
			if (old_section.get_ofs() % self.align > 0):
				self.put_debug('Padding section "%s" (current size: 0x%06X) for relocation...' % (old_section.name, old_section.get_ofs()))
				while (old_section.get_ofs() % self.align > 0):
					old_section.store.w8(0x00)
			
			# Put new section after previous one
			relocation_offset = old_section.relocation_offset + old_section.get_ofs()
			if (relocation_offset != section.relocation_offset):
				self.put_debug('Relocated section "%s" after "%s" to offset 0x%06X' % (section.name, old_section.name, relocation_offset))
				section.relocation_offset = relocation_offset
				relocated = True
			
			# Continue
			old_section = section
		
		return relocated
	
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
			
			self.put_debug('Relocating ROM sections...')
			relocated1 = self.relocate(ROM_SECTIONS)
			self.put_debug('Relocating RAM sections...')
			relocated2 = self.relocate(RAM_SECTIONS)
			
			relocated = True if relocated1 or relocated2 else False
			
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
	
	
	def _assemble(self, text, pc=None, echo_lines=False):
		"""Dirty assembly text parser"""
		
		#if pc is None:
		#	pc = self.pc
		#else:
		#	self.pc = pc
		if (pc is not None) and (pc != self.section.get_address()):
			# While testing BRANCH instructions, it is crucial to force a specific value for PC to check displacement encoding
			# But better shout out what's going on, because it might lead to bad bugs if it happens unnoticed.
			
			self.put_debug('Forcing address of section "%s" from 0x%06X to 0x%06X' % (self.section.name, self.section.get_address(), pc))
			self.section.relocation_offset += pc - self.section.get_address()
			#self.section.base_address += pc - self.section.base_address
		
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
			
			if echo_lines:
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
				self.enter_section('.text')
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
					
					# Handle expression
					expression = None
					if '+' in w: expression = '+'
					if '-' in w: expression = '-'
					if expression is not None:
						# Omit the expression in name
						label_name = w[:w.index(expression)]
					else:
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
					
					# Handle expression afterwards
					if expression is not None:
						v = int(w[w.index(expression)+1:])
						self.put_debug('Handling expression (0x%06X %s %d)...' % (label_addr, expression, v))
						if expression == '+':
							label_addr += v
						elif expression == '-':
							label_addr -= v
						else:
							raise SyntaxError('Unsupported expression: "%s"' % w)
					
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
			elif mnem == '.double':
				self.w32((0x100000000 + params[0]) % 0x100000000)
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
				
			
			### CR16B instructions
			elif mnem == 'nop':
				self.assemble_nop()
			elif mnem == 'di':
				self.w16(0x7dde)
			elif mnem == 'ei':
				self.w16(0x7dfe)
			elif mnem == 'res':
				#self.w16(0x1514)
				self.w16(0x1520)
			elif mnem == 'wait':
				self.w16(0x7ffe)
			elif mnem == 'eiwait':
				self.w16(0x7fe6)
			elif mnem in ['lpr', 'spr']:
				if mnem == 'lpr':
					op = 0b1000
					reg = str_to_reg(params[0])
					sr = params[1]
				elif mnem == 'spr':
					op = 0b1001
					reg = str_to_reg(params[1])
					sr = params[0]
				
				if   sr == 'cfg': v = 0x05
				elif sr == 'intbaseh': v = 0x04
				elif sr == 'intbasel': v = 0x03
				elif sr == 'isp': v = 0x0b
				elif sr == 'psr': v = 0x01
				else: raise ValueError('Unknown internal value %s' % sr)
				self.assemble_special(op=op, p1=v, p2=reg)
			
			# SBIT,CBIT, TBIT, STORi $imm4, X
			elif mnem[:4] in ('sbit', 'cbit'):
				i = str_to_format(mnem) # byte or word
				src_imm = params[0]
				dest_disp = params[1]
				ex_op = 0b00
				if mnem[:4] == 'sbit': ex_op = 0b01
				elif mnem[:4] == 'cbit': ex_op = 0b00
				
				if type(dest_disp) is int:
					# SBIT imm, abs
					self.w32(
						  ((dest_disp & 0b001111111111111111) << 16)\
						| (0b00 << 14)\
						| (i << 13)\
						| (0b0010 << 9)\
						| (((dest_disp & 0b100000000000000000) >> 17) << 8)\
						| (ex_op << 6)\
						| (((dest_disp & 0b010000000000000000) >> 16) << 5)\
						| (src_imm << 1)\
						| 0b0
					)
				else:
					raise TypeError('Unsupported SBIT displacement: %s' % str(dest_disp))
				
			elif mnem == 'tbit':
				dest_reg = str_to_reg(params[1])
				
				if type(params[0]) is int:
					# TBIT x, Ry
					imm5 = params[0]
					i = 1
					op = 0b1011
					#self.assemble_basic_imm_reg(op=0b11, i=1, imm=imm, dest_reg=reg)
					self.w16(
						  (0b00 << 14)\
						| (i << 13)\
						| (op << 9)\
						| (dest_reg << 5)\
						| imm5
					)
				else:
					src_reg = str_to_reg(params[0])
					self.assemble_basic_reg_reg(op=0b1011, i=1, src_reg=src_reg, dest_reg=dest_reg)
					#raise TypeError('Unsupported params for TBIT: %s, %s' % (params[0], params[1]))
				
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
						elif ',' in params[1][1]:
							# STOR reg, disp+regs
							self.assemble_stor(i=i,	src_reg=str_to_reg(params[0]), src_imm=None,	dest_reg=str_to_reg(params[1][1][1:-1].split(',')[1]), dest_disp=params[1][0], dest_reg_is_far=True	)
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
				
				#@FIXME: params[1] can also be a pair! e.g. "mulsw r2, (r9,r8)"
				if ',' in params[1]: raise TypeError('Regpair not yet supported for "%s" with param %s' % (mnem, params[1]))
				dest_reg = str_to_reg(params[1])
				
				if type(params[0]) is int:
					imm = params[0]
					
					# Handle "forced WORD", e.g. "movw $0x0000, r12" => uses medium size!
					force_word = False
					"""
					if mnem == 'movw':
						imm_str = words[1].split(',')[0]
						if len(imm_str) == 7:	# "$0xXXXX" = len 7
							#self.put_debug('Forced WORD')
							force_word = True
					"""
					self.assemble_basic_imm_reg(op=op, i=i, imm=imm, dest_reg=dest_reg, force_word=force_word)
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
			
			
			#elif mnem == 'beq0b':	self.assemble_brcondi(cond=COND_EQ, val1=0, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			#elif mnem == 'beq1b':	self.assemble_brcondi(cond=COND_EQ, val1=1, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			#elif mnem == 'bne0b':	self.assemble_brcondi(cond=COND_NE, val1=0, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			#elif mnem == 'bne1b':	self.assemble_brcondi(cond=COND_NE, val1=1, i=I_BYTE, reg=str_to_reg(params[0]), disp5m1=params[1] - pc)
			elif (len(mnem) == 5) and (mnem[:3] in ('beq', 'bne')):	# Special compare-and-branch (beq0/1b/2)
				self.assemble_brcondi(
					cond=COND_NE if mnem[1:3] == 'ne' else COND_EQ,	# condition: eq or ne
					val1=int(mnem[3:4]),	# val: 0 or 1
					i=I_WORD if mnem[-1:] == 'w' else I_BYTE,	# format: b or w
					reg=str_to_reg(params[0]),	# register
					disp5m1=params[1] - pc	# displacement
				)
			
			elif (mnem[:1] == 'b') and (mnem[1:] in CONDS):	# beq, bne, ...
				addr = params[0]
				disp = params[0] - pc
				self.assemble_br(disp=disp, cond=CONDS[mnem[1:]])
			
			elif mnem == 'br':
				addr = params[0]
				disp = params[0] - pc
				self.assemble_br(disp=disp)	# cond=0x0e
			
			elif mnem == 'jump':
				self.assemble_jump(reg_pair=str_to_reg(params[0][1:-1].split(',')[1]))
			
			elif (mnem[:1] == 'j') and (mnem[1:] in CONDS):	# jcs, ...
				#self.assemble_jump(reg_pair=str_to_reg(params[0][1:-1].split(',')[1]), cond=CONDS[mnem[1:]])
				reg_pair = str_to_reg(params[0][1:-1].split(',')[1])
				cond = CONDS[mnem[1:]]
				self.w16(
					  (0b00010110 << 8)\
					| (cond << 5)\
					| (reg_pair << 1)\
					| 1
				)
			
			elif mnem == 'jal':
				self.assemble_jal(
					lnk_pair=str_to_reg(params[0][1:-1].split(',')[1]),
					target_pair=str_to_reg(params[1][1:-1].split(',')[1])
				)
			
			elif (mnem[:1] == 's') and (mnem[1:] in CONDS):	# seq, sne, ...
				reg = str_to_reg(params[0])
				cond = CONDS[mnem[1:]]
				self.assemble_special(op=0b111, p1=cond, p2=reg)
				
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
	
	
	def assemble_basic_imm_reg(self, op, i, imm, dest_reg, force_word=False):
		"""Basic instruction involving an immediate and a register. Automatically handles the size."""
		
		#@FIXME: Need to check unsigned/signed
		if (i == I_BYTE) and (imm >= 0x80):
			imm = imm - 0x100
		if (i == I_WORD) and (imm >= 0x8000):
			imm = imm - 0x10000
		
		#if (i==I_BYTE) and ((imm == -16) or (imm >= -14 and imm <= 15)):	# and (not is_medium):
		#@FIXME: According to the manual the only allowed values for imm5 are: -16, -14...15 (note: no -15 !)
		if ((imm == -16) or (imm >= -14 and imm <= 15)) and (not force_word):
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
		
	def assemble_stor(self, i, src_reg, src_imm, dest_reg, dest_disp, dest_reg_is_far=False):
		
		#@TODO: STOR with register-relative and no displacement and 4-bit immediate
		#self.assemble_stor_rr(reg= , imm4=params[0])
		
		#@TODO: STOR with register-relative and 16-bit displacement and 4-bit immediate
		#self.assemble_stor_rr16(reg=..., disp16=... , imm4=params[0])
		
		#@TODO: STOR with absolute 18-bit address and 4-bit immediate
		#self.assemble_stor_abs(ad18=params[1], imm4=params[0])
		
		if (src_reg is None) and (dest_reg is None):
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
			
		elif (src_reg is None) and (dest_reg is not None) and (dest_disp is not None):
			
			# see B.2.5
			if   dest_reg == REG_R0: bs = 0b00
			elif dest_reg == REG_R1: bs = 0b01
			elif dest_reg == REG_R8: bs = 0b10
			elif dest_reg == REG_R9: bs = 0b11
			else:
				raise TypeError('Unsupported register for register-relative STOR')
			
			if (dest_disp == 0) and (src_imm < 16):
				self.w16(
					  (0b01 << 14)\
					| (i << 13)\
					| (0b0010 << 9)\
					| ((bs & 0b10) << 8)\
					| (0b11 << 6)\
					| ((bs & 0b01) << 5)\
					| (src_imm << 1)\
					| 1
				)
			else:
				# B2.5 Register-relative with 16-bit displacement
				self.w32(
					  (dest_disp << 16)\
					| (0b00 << 14)\
					| (i << 13)\
					| (0b0010 << 9)\
					| ((bs & 0b10) << 8)\
					| (0b11 << 6)\
					| ((bs & 0b01) << 5)\
					| (src_imm << 1)\
					| 1
				)
		
		elif (src_reg is not None) and (dest_reg is None):
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
		elif (src_reg is not None) and (dest_reg is not None) and (dest_disp is not None):
			# Reg to Reg-relative
			if (abs(dest_disp) < 32) and (not dest_reg_is_far):
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
					| ((0b11 if dest_reg_is_far else 0b10) << 11)\
					| (((dest_disp & 0b110000000000000000) >> 16) << 9)\
					| (src_reg << 5)\
					| (dest_reg << 1)\
					| (0b1)
				)
			else:
				raise ValueError('Large register-relative STOR displacements are not yet supported, sorry!')
		else:
			raise TypeError('Parameter combination for STOR not yet supported: src_reg=%s, src_imm=%s, dest_reg=%s, dest_disp=%s, dest_reg_is_far=%s' % (src_reg, src_imm, dest_reg, dest_disp, dest_reg_is_far))
		
	
	def assemble_br(self, disp, cond=0x0e):
		"""Assemble a branch with condition with given displacement, automatically choses the instruction size.
			cond:
				1=NE
				
				0xe=no condition
		"""
		
		
		#@FIXME: Something is broken here!
		#@FIXME: For short to work, we have to take address "overflows" into account?!?
		
		if disp < 0:
			# Backwards jump
			#@FIXME: This is done by trial and error
			self.assemble_br_medium(disp=disp + 0x200000, cond=cond)	#0x0e)
		
			"""
		elif (disp == 8):
			# Special case for super-even jumps?
			pc = self.section.get_address()
			self.put('@FIXME: br with cond=%02X to 0x%06X + %d = 0x%06X' % (cond, pc, disp, pc+disp))
			#	cond=0x7, disp=0x08 => F8 5E = 5EF8 = 01 0 1111 0111 1100 0 = B7=BLE
			#	cond=0x4, disp=0x20 => 80 42 = 4280
			self.w16(
				  (0b010 << 13)\
				| (0b1 << 12)\
				| (cond << 9)\
				| (0b01111 << 4)\
				| (disp & 0b000001111)	# disp0 must be zero / even
			)
			"""
		
		elif ((disp & 1) == 0) and ((disp >= -256) and (disp <= 254)):
			# Short jumps must be even
			
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
			| (disp & 0b000011111)	# disp0 must be zero / even
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
	def assemble_brcondi(self, cond, val1, i, reg, disp5m1):
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
	
	def assemble_jal(self, lnk_pair, target_pair):
		self.w16(
			  (0b0001011 << 9)\
			| (lnk_pair << 5)\
			| (target_pair << 1)\
			| 0
		)
	
	#@TODO: Bit manipulation
	

if __name__ == '__main__':
	
	"""
	import sys
	
	
	if len(sys.argv) < 2:
		put('No argument given, running test(s)...')
		
		# Enable what to do, e.g. do assembler self-tests or actually try assembling and patching something
		#test_manual_assembly()
		#test_text_parser()
		#test_instructions()
		test_reassemble()
		
		#run_patch()
		
		sys.exit()
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
		# Dump stats
		
		put('Constants:')
		for k,c in asm.constants.items():
			put('\t* %s: 0x%06X / %d' % (k, c, c))
		
		#put('Sections:')
		#for k,section in asm.sections.items():
		#	put('\t* %s at 0x%06X: %s' % (section.name, section.base_address, ' '.join(['%02X'%b for b in section.store.get_data()])) )
		
		MAX_DUMP_SIZE = 0x20
		def is_printable(s):
			for i,c in enumerate(s[:MAX_DUMP_SIZE]):
				if c in [10,13]: continue	# Potentially printable
				if (i == len(s)-1) and (c == 0): continue	# C-string terminator
				
				if c not in range(32, 127): return False
			return True
		
		def show_section_stats(section):
			data = section.store.get_data()
			l = len(data)
			put('\t* %s at address 0x%06X+%d (size: 0x%04X / %d bytes): %s%s' % (section.name, section.base_address, section.relocation_offset, l,l, ' '.join(['%02X'%b for b in data[:MAX_DUMP_SIZE]]), '...' if l > MAX_DUMP_SIZE else '') )
			#put('\t* %s at address 0x%06X+%d (size: 0x%04X / %d bytes): %s%s' % (section.name, section.base_address, section.relocation_offset, l,l, str(bytes(data[:MAX_DUMP_SIZE])), '...' if l > MAX_DUMP_SIZE else '') )
			for label_name, label_ofs in section.labels.items():
				label_addr = section.get_label_address(label_name)
				label_ofs = section.labels[label_name]
				label_size = l
				label_keys = list(section.labels.keys())
				i = label_keys.index(label_name)
				if i+1 < len(section.labels):
					label_size = section.get_label_address(label_keys[i+1]) - label_addr
				label_data = data[label_ofs:label_ofs+label_size]
				
				if label_size == 0:				label_data_str = '--'
				elif is_printable(label_data):	label_data_str = '%s%s' % (str(bytes(label_data[:MAX_DUMP_SIZE])), '...' if label_size > MAX_DUMP_SIZE else '')
				else:							label_data_str = '%s%s' % (' '.join(['%02X'%b for b in label_data[:MAX_DUMP_SIZE]]), '...' if label_size > MAX_DUMP_SIZE else '')
				put('\t\t+ %s at ofs 0x%04X (addr: 0x%04X, size: 0x%04X / %d bytes): %s' % (label_name, label_ofs, label_addr, label_size,label_size, label_data_str ))
		
		found = False
		for name in ROM_SECTIONS:
			if not name in asm.sections: continue
			if not found:	# Print header only on demand
				put('ROM Sections:')
				found = True
			show_section_stats(asm.sections[name])
		if not found: put('(no ROM sections)')
		
		found = False
		for name in RAM_SECTIONS:
			if not name in asm.sections: continue
			if not found:	# Print header only on demand
				put('RAM Sections:')
				found = True
			show_section_stats(asm.sections[name])
		if not found: put('(no RAM sections)')
		
		found = False
		for name,section in asm.sections.items():
			if (name in ROM_SECTIONS) or (name in RAM_SECTIONS): continue
			if not found:	# Print header only on demand
				put('Unknown Sections:')
				found = True
			show_section_stats(section)
		
	
	if output_filename is None:
		put('Dumping (stdout)...')
		asm.dump()
		#put(' '.join(['%02X'%b for b in bin]))
	else:
		bin = asm.get_bytes()
		
		put('Writing output file "%s" (0x%06X / %d bytes used)...' % (output_filename, len(bin), len(bin)))
		with open(output_filename, 'wb') as h:
			h.write(bin)
			if pad is not None:
				l = pad - len(bin)
				if l >= 0:
					put('Padding %d bytes to fill up 0x%06X / %d bytes' % (l, pad,pad))
					h.write(bytes([0] * l))
				else:
					put('Produced data exceeds padding! (%d > %d)' % (len(bin), pad))
	
	# EOF
