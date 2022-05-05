#!/usr/bin/python3
"""
National Semiconductors
CR16A/CR16B disassembler

Based on the great work of the MAME project
	https://github.com/mamedev/mame/tree/master/src/devices/cpu/cr16b
	license:BSD-3-Clause
	copyright-holders:AJR

Check against MAME:
	mame -debug -rompath /z/apps/_emu/_roms gl8008cx

BUG:
	* "ashuw" seems to not resolve correctly: Should result in -15..15, not "$65521"
		e.g. at 0017C0:	91 28 F1 FF	2891 FFF1	ashuw   $65521, r4


2022-02-23 Bernhard "HotKey" Slawik
"""

RS232_ADDR = 0xFB90
ROM_OFFSET = 0x80000	# Where in address space is the first ROM byte located? I think 0x80000+


# Those are just speculation for now and are used to make some memory accesses "pop out" in the disassembly
KNOWN_ADDRS = {
	#0x020E: 'CODE: SHUTDOWN',	# on GL8008CX:
	
	0xB700: 'GL8008CX:SP',
	0xB800: 'GL8008CX:ISR',
	
	# Load strings externally. It's too many of them.
	ROM_OFFSET: 'ROM_OFFSET',
	
	# boardCR16.h:
	0xD700: 'TMON_START',
	0xFB40: 'BCR_ADDR',
	0xFB90: 'RS232_ADDR',
	0xFB38: 'DIP_SWITCH_ADDR',
	0xFB44: 'SHCFG_ADDR',
	0xFB42: 'ISEIR',
	0xF912: 'DBGCFG',
	0xF902: 'IOCFG',
	0xF904: 'SZCFG0',
	0xF906: 'SZCFG1',
	0xF908: 'SZCFG2',
	0xFBA0: 'LED_PORT_ADDR',
	
	# boardCR16B.h:
	0xE600: 'SWITCH_START',
	0xE700: 'TMON_START [B]',
	0x80000: 'RAM_OFFSET',
	0xDFFF: 'SRAM_END',
	0xFB80: 'RS422_ADDR',
	0xFB90: 'RS232_ADDR',
	0xFB90: 'RS232_RBR_ADDR',
	0xFB92: 'RS232_IER_ADDR',
	0xFB96: 'RS232_LCR_ADDR',
	0xFB9A: 'RS232_LSR_ADDR',
	0xFF24: 'DBGTXLOC_ADDR',
	0xFF22: 'DBGTXST_ADDR',
	0xFF26: 'DBGTINT_ADDR',
	0xFF10: 'DBGTXD_ADDR',
	0xFF20: 'DBGRXST_ADDR',
	0xFF00: 'FF00 (DBGRXD_ADDR)',
	0xFF2A: 'DBGISESRCA_ADDR',
	0xFF28: 'DBGABORT_ADDR',
	0xF004: 'DIP_SWITCH_ADDR [B]',
	
	0xF006: 'SysCtrl_Addr',
	0xF012: 'IcuCtrl_Addr',
	0xF014: 'IcuSta_Addr',
	0xF016: 'IcuMask_Addr',
	#0xFB40: 'BCR_ADDR',
	#0xFB44: 'SHCFG_ADDR',
	#0xFB42: 'ISEIR',
	0xF002: 'LED_PORT1_ADDR',
	0xF003: 'LED_PORT2_ADDR',
	
	#commRS232.h:
	(RS232_ADDR+0x0): 'RS232_RBR_ADDR',
	(RS232_ADDR+0x2): 'RS232_IER_ADDR',
	(RS232_ADDR+0x4): 'RS232_FCR_ADDR',
	(RS232_ADDR+0x6): 'RS232_LCR_ADDR',
	(RS232_ADDR+0x8): 'RS232_MCR_ADDR',
	(RS232_ADDR+0xA): 'RS232_LSR_ADDR',
	
}

# Merge strings we found using "strings"
from ROM_GL8008CX_strings import STRINGS
for addr, txt in STRINGS.items():
	KNOWN_ADDRS[ROM_OFFSET + addr] = 'STRING "%s"' % txt
	#KNOWN_ADDRS[addr] = 'STRING0 "%s"' % txt

### Glue
# Disassembler constants for the return value (src/lib/util/disasmintf.h)
SUPPORTED       = 0x80000000	# are disassembly flags supported?
STEP_OUT        = 0x40000000	# this instruction should be the end of a step out sequence
STEP_OVER       = 0x20000000	# this instruction should be stepped over by setting a breakpoint afterwards
OVERINSTMASK    = 0x18000000	# number of extra instructions to skip when stepping over
OVERINSTSHIFT   = 27			# bits to shift after masking to get the value
LENGTHMASK      = 0x0000ffff	# the low 16-bits contain the actual length


def BIT(v, b):
	return ((v & (2**b)) > 0)

s16 = lambda v: v
u32 = lambda v: v

class Stream:
	def __init__(self):
		self.r = ''
	def push(self, t):
		self.r += t
	def format(self, fs, *args):
		self.r += fs % args
	def dump(self):
		r = self.r
		self.r = ''	# Clear
		return r

class DataBuffer:
	"""Analogon to cr16b_disassembler::data_buffer"""
	def __init__(self, data, addr_offset=0x0000):
		self.data = data
		self.addr_offset = addr_offset
		#self.ofs = 0
	def r8(self, ofs):
		r = self.data[ofs - self.addr_offset]	#self.ofs]
		#self.ofs += 1
		return r
		
	def r16(self, ofs):
		#@FIXME: Which endianness?
		#return self.r8() * 256 + self.r8()
		#return self.r8(ofs) * 256 + self.r8(ofs+1)
		return self.r8(ofs+1) * 256 + self.r8(ofs)



# cr16_arch
ARCH_CR16A = 0
ARCH_CR16B = 1

class CR16B_Disassembler:
	# Condition codes
	s_cc = [	#const char *const[14]
		"eq", "ne",
		"cs", "cc",
		"hi", "ls",
		"gt", "le",
		"fs", "fc",
		"lo", "hs",
		"lt", "ge"
	]
	
	def __init__(self, arch=ARCH_CR16B):
		self.m_arch = arch
		self.addrs_found = {}
	
	def emit_addr(self, addr=None, disp=None, imm=None, pc=0):
		"""Register the use of an address, so we can keep track"""
		if addr is not None:
			pass
		elif disp is not None:
			addr = disp
		elif imm is not None:
			addr = imm
		else:
			put('NOTHING GIVEN TO EMIT!')
			return
		
		# Ignore 0
		#if addr == 0: return
		
		if addr in KNOWN_ADDRS:
			put('! Address 0x%06X uses known address 0x%06X = %s' % (pc, addr, KNOWN_ADDRS[addr]))
		else:
			#put('0x%06X uses address 0x%06X' % (pc, addr))
			pass
		
		#if not addr in self.addrs_found: self.addrs_found.append(addr)
		if addr in self.addrs_found:
			self.addrs_found[addr].append(pc)
		else:
			self.addrs_found[addr] = [ pc ]
	
	def opcode_alignment(self):
		return 2
	
	def format_reg(self, stream, reg):	# u8 reg
		if (reg == 15):
			stream.push("sp")
		elif (reg == 14):
			stream.push("ra")
		elif (reg == 13) and (self.m_arch != ARCH_CR16A):
			stream.push("era")	# R13 in SMM
		else:
			stream.format("r%d", reg)
	
	def format_rpair(self, stream, reg):	# u8 reg
		if (reg == 13) and (self.m_arch != ARCH_CR16A):
			stream.push("(ra,era)")
		else:
			stream.format("(r%d,r%d)", reg + 1, reg)
	
	def format_rproc(self, stream, reg):	# u8 reg
		if reg == 1: stream.push("psr")
		elif reg == 3: stream.push("intbasel")
		elif reg == 4: stream.push("intbaseh")
		elif reg == 5: stream.push("cfg")
		elif reg == 7: stream.push("dsr")
		elif reg == 9: stream.push("dcr")
		elif reg == 11: stream.push("isp")
		elif reg == 13: stream.push("carl")
		elif reg == 14: stream.push("carh")
		else:
			stream.push("res")
	
	def format_short_imm(self, stream, imm):	# u8 imm
		# 5-bit short immediate value (0 to 15, -16, -14 to -1)
		if (imm == 0):
			stream.push("$0")
			v = 0
		elif (imm >= 0x10):
			v = 0x10 - (imm & 0x0f)
			stream.format("$-0x%X", v)
			v = -v
		else:
			v = imm
			stream.format("$0x%X", v)
		return v
	
	def format_short_imm_unsigned(self, stream, imm, i):	# u8 imm, bool i
		if (imm == 0):
			stream.push("$0")
			v = 0
		elif (i):
			v = (0xfff0 | (imm & 0x0f)) if (imm >= 0x10) else imm
			stream.format("$0x%04X", v)
		else:
			v = (0xf0 | (imm & 0x0f)) if (imm >= 0x10) else imm
			stream.format("$0x%02X", v)
		return v
	
	def format_short_imm_decimal(self, stream, imm):	# u8 imm
		if (imm >= 0x10):
			v = 0x10 - (imm & 0x0f)
			stream.format("$-%d", v)
			v = -v
		else:
			v = imm
			stream.format("$%d", v)
		return v
	
	def format_medium_imm(self, stream, imm):	# u16 imm
		if (imm >= 0x8000):
			v = 0x10000 - imm
			stream.format("$-0x%X", v)
			v = -v
		else:
			v = imm
			stream.format("$0x%X", v)
		return v
	
	def format_medium_imm_unsigned(self, stream, imm, i):	# u16 imm, bool i
		if (i):
			v = imm
			stream.format("$0x%04X", v)
		else:
			v = imm & 0xff
			stream.format("$0x%02X", v)
		return v
	
	def format_medium_imm_decimal(self, stream, imm):	# u16 imm
		v = s16(imm)
		stream.format("$%d", v)
		return v
	
	def format_imm21(self, stream, imm):	# u32 imm
		v = imm
		stream.format("$0x%06X", v)
		return v
	
	def format_disp5(self, stream, disp):	# u8 disp
		# 5-bit short displacement (0 to 15, 16 to 30 even)
		if (disp == 0):
			stream.push("0")
			v = 0
		else:
			v = disp
			stream.format("0x%X", v)
		return v
	
	def format_disp16(self, stream, disp):	# u16 disp
		# 16-bit displacement (0 to 64K-1)
		v = disp
		stream.format("0x%X", v)
		return v
	
	def format_disp18(self, stream, disp):	# u32 disp
		# 18-bit medium displacement (-128K to 128K-1 or 0 to 256K-1, result truncated to 18 bits)
		if (disp == 0):
			stream.push("0")
			v = 0
		elif (disp >= 0x20000):
			v = 0x40000 - disp
			stream.format("-0x%X", v)
			v = -v
		else:
			v = disp
			stream.format("0x%X", v)
		return v
	
	def format_abs18(self, stream, addr):	# u32 addr
		# 18-bit absolute (any memory location within first 256K)
		v = addr
		stream.format("0x%05X", v)
		return v
	
	def format_pc_disp5(self, stream, pc, disp):	# offs_t pc, u8 disp
		if (self.m_arch == ARCH_CR16A):
			v = ( (pc + 0x20 - disp) if (disp >= 0x10) else (pc + disp)) & 0x1ffff	# SMM
			stream.format("0x%05X", v)
		else:
			v = ( (pc + 0x20 - disp) if (disp >= 0x10) else (pc + disp)) & 0x1fffff	# LMM
			stream.format("0x%06X", v)
		return v
	
	def format_pc_disp9(self, stream, pc, disp):	# offs_t pc, u16 disp
		if (self.m_arch == ARCH_CR16A):
			v = ( (pc + 0x200 - disp) if (disp >= 0x100) else (pc + disp)) & 0x1ffff	# SMM
			stream.format("0x%05X", v)
		else:
			v = ( (pc + 0x200 - disp) if (disp >= 0x100) else (pc + disp)) & 0x1fffff	# LMM
			stream.format("0x%06X", v)
		return v
	
	def format_pc_disp17(self, stream, pc, disp):	# offs_t pc, u32 disp
		v = ( (pc + 0x20000 - disp) if (disp >= 0x10000) else (pc + disp)) & 0x1ffff
		stream.format("0x%05X", v)
		return v
	
	def format_pc_disp21(self, stream, pc, disp):	# offs_t pc, u32 disp
		v = (pc + ((disp & 0x0ffffe) | (disp & 0x000001) << 20)) & 0x1fffff
		stream.format("0x%06X", v)
		return v
	
	def format_excp_vector(self, stream, vec):	# u8 vec
		if vec == 0x05: # Supervisor call
			stream.push("svc")
		elif vec == 0x06: # Division by zero
			stream.push("dvz")
		elif vec == 0x07: # Flag
			stream.push("flg")
		elif vec == 0x08: # Breakpoint
			stream.push("bpt")
		elif vec == 0x0a: # Undefined instruction
			stream.push("und")
		elif vec == 0x0e: # Debug
			stream.push(("dbg" if (self.m_arch != ARCH_CR16A) else "und ; reserved"))
		else:
			stream.push("und ; reserved")
	
	# offs_t cr16b_disassembler::disassemble(self, stream, offs_t pc, const cr16b_disassembler::data_buffer &opcodes, const cr16b_disassembler::data_buffer &params)
	def disassemble(self, stream, pc, opcodes):	#, params):
		opcode = opcodes.r16(pc)	# u16 opcode
		
		if (BIT(opcode, 15)):
			# Load and store group (excluding LOADM, STORM)
			if (BIT(opcode, 14)):
				stream.format("stor%c   ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				stream.push(", ")
			else:
				stream.format("load%c   ", 'w' if BIT(opcode, 13) else 'b')
			
			o = opcode & 0x1801
			if o == 0x1001:
				disp = self.format_disp18(stream, u32(opcode & 0x0600) << 7 | opcodes.r16(pc + 2))
				stream.push("(")
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(")")
				self.emit_addr(disp=disp, pc=pc)	# Often 0, 2, ...
				
				if (not BIT(opcode, 14)):
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 4 | SUPPORTED
			
			elif o == 0x1801:
				if ((opcode & 0x001e) == 0x001e):
					addr = self.format_abs18(stream, u32(opcode & 0x0600) << 7 | opcodes.r16(pc + 2))
					self.emit_addr(addr=addr, pc=pc)
				else:
					disp = self.format_disp18(stream, u32(opcode & 0x0600) << 7 | opcodes.r16(pc + 2))
					self.format_rpair(stream, (opcode & 0x001e) >> 1)
					self.emit_addr(disp=disp, pc=pc)
				
				if (not BIT(opcode, 14)):
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 4 | SUPPORTED
			
			else:
				disp = self.format_disp5(stream, (opcode & 0x1e00) >> 8 | (opcode & 0x0001))
				stream.push("(")
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(")")
				self.emit_addr(disp=disp, pc=pc)	# Often 0, 2, ...
				if (not BIT(opcode, 14)):
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
		
		else:
			#switch (opcode & 0x7e01)
			o = (opcode & 0x7e01)
			if o in (0x0000, 0x0001, 0x2000, 0x2001):
				stream.format("add%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x0200, 0x0201, 0x2200, 0x2201):
				#@TODO: 0x0000 = NOP = ADDB $0, r0
				
				if (opcode == 0x0200): # NOP = ADDU $0, R0
					stream.push("nop")
				else:
					stream.format("addu%c   ", 'w' if BIT(opcode, 13) else 'b')
					if ((opcode & 0x001f) == 0x0011):
						imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
						self.emit_addr(imm=imm, pc=pc)
						stream.push(", ")
						self.format_reg(stream, (opcode & 0x01e0) >> 5)
						return 4 | SUPPORTED
					else:
						imm = self.format_short_imm(stream, opcode & 0x001f)
						self.emit_addr(imm=imm, pc=pc)
						stream.push(", ")
						self.format_reg(stream, (opcode & 0x01e0) >> 5)
						return 2 | SUPPORTED
				return 2 | SUPPORTED
			
			elif o in (0x0400, 0x0401, 0x2400, 0x2401,	0x4401, 0x6401):
				# Bit manipulation and store immediate (memory operand)
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
					return 2 | SUPPORTED
				
				o2 = opcode & 0x00c0
				if o2 == 0x0000:
					stream.format("cbit%c   $%d", 'w' if BIT(opcode, 13) else 'b', (opcode & 0x001e) >> 1)
				elif o2 == 0x0040:
					stream.format("sbit%c   $%d", 'w' if BIT(opcode, 13) else 'b', (opcode & 0x001e) >> 1)
				elif o2 == 0x0080:
					stream.format("tbit%c   $%d", 'w' if BIT(opcode, 13) else 'b', (opcode & 0x001e) >> 1)
				elif o2 == 0x00c0:
					stream.format("stor%c   ", 'w' if BIT(opcode, 13) else 'b')
					self.format_short_imm(stream, (opcode & 0x001e) >> 1)	# unsigned 4-bit value
				
				if (BIT(opcode, 14)):
					stream.push(", 0(")
					self.format_reg(stream, (opcode & 0x0120) >> 5)
					stream.push(")")
					return 2 | SUPPORTED
				else:
					stream.push(", ")
					if (BIT(opcode, 0)):
						disp = self.format_disp16(stream, opcodes.r16(pc + 2))
						stream.push("(")
						self.format_reg(stream, (opcode & 0x0120) >> 5)
						stream.push(")")
						self.emit_addr(disp=disp, pc=pc)	# Often 0, 2, ...
					else:
						addr = self.format_abs18(stream, u32(opcode & 0x0100) << 9 | u32(opcode & 0x0020) << 11 | opcodes.r16(pc + 2))
						self.emit_addr(addr=addr, pc=pc)
					return 4 | SUPPORTED
			
			elif o in (0x0600, 0x0601, 0x2600, 0x2601):
				stream.format("mul%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x0800, 0x0801, 0x2800, 0x2801):
				stream.format("ashu%c   ", 'w' if BIT(opcode, 13) else 'b')
				#@FIXME: Instead of "ashuw $65521" it should emit an offset -15..15
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_decimal(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_decimal(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x0a00, 0x0a01, 0x2a00, 0x2a01):
				stream.format("lsh%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_decimal(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_decimal(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x0c00, 0x0c01, 0x2c00, 0x2c01):
				stream.format("xor%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_unsigned(stream, opcodes.r16(pc + 2), BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_unsigned(stream, opcode & 0x001f, BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x0e00, 0x0e01, 0x2e00, 0x2e01):
				stream.format("cmp%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x1000, 0x1001, 0x3000, 0x3001):
				stream.format("and%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_unsigned(stream, opcodes.r16(pc + 2), BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_unsigned(stream, opcode & 0x001f, BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x1200, 0x1201, 0x3200, 0x3201):
				stream.format("addc%c   ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o == 0x1400:
				# Conditional or unconditional branch to small address
				if ((opcode & 0x000e) == 0x000e) and ((opcode & 0x01e0) != 0x01e0):
					addr = u32(opcode & 0x0010) << 12 | opcodes.r16(pc + 2)
					if ((opcode & 0x01e0) == 0x01c0):
						stream.push("br      ")
						disp = self.format_pc_disp17(stream, pc, addr)
						stream.push('\n')	# new line for "end of block"
						self.emit_addr(disp=disp, pc=pc)
					else:
						stream.format("b%s     ", self.s_cc[(opcode & 0x01e0) >> 5])
						disp = self.format_pc_disp17(stream, pc, addr)
						self.emit_addr(disp=disp, pc=pc)
					return 4 | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o in (0x1401, 0x3401):
				# Compare and branch group
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
				else:
					stream.format("b%s%c%c   ", "ne" if (BIT(opcode, 7)) else "eq", '1' if (BIT(opcode, 6)) else '0', 'w' if BIT(opcode, 13) else 'b')
					self.format_reg(stream, (opcode & 0x0120) >> 5)
					stream.push(", ")
					disp = self.format_pc_disp5(stream, pc, opcode & 0x001e)
					self.emit_addr(disp=disp, pc=pc)
				return 2 | SUPPORTED
			
			elif o == 0x1600:
				# Jump and link to large address
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
				else:
					stream.push("jal     ")
					self.format_rpair(stream, (opcode & 0x01e0) >> 5)
					stream.push(", ")
					self.format_rpair(stream, (opcode & 0x001e) >> 1)
				return 2 | SUPPORTED
			
			elif o == 0x1601:
				if ((opcode & 0x01e0) != 0x01e0) and (self.m_arch != ARCH_CR16A):
					r = (opcode & 0x001e) >> 1
					if ((opcode & 0x01e0) == 0x01c0):
						stream.push("jump    ")
						self.format_rpair(stream, r)
						stream.push('\n')	# new line for "end of block"
					else:
						stream.format("j%s     ", self.s_cc[(opcode & 0x01e0) >> 5])
						self.format_rpair(stream, r)
					return 2 | (STEP_OUT if (opcode == 0x17db) else  0) | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o in (0x1800, 0x1801, 0x3800, 0x3801):
				stream.format("mov%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_unsigned(stream, opcodes.r16(pc + 2), BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_unsigned(stream, opcode & 0x001f, BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x1a00, 0x1a01, 0x3a00, 0x3a01):
				stream.format("subc%c   ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x1c00, 0x1c01, 0x3c00, 0x3c01):
				stream.format("or%c     ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_unsigned(stream, opcodes.r16(pc + 2), BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_unsigned(stream, opcode & 0x001f, BIT(opcode, 13))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x1e00, 0x1e01, 0x3e00, 0x3e01):
				stream.format("sub%c    ", 'w' if BIT(opcode, 13) else 'b')
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o == 0x3400:
				# Branch and link to small address
				if ((opcode & 0x000e) == 0x000e):
					stream.push("bal     ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					stream.push(", ")
					disp = self.format_pc_disp17(stream, pc, u32(opcode & 0x0010) << 12 | opcodes.r16(pc + 2))
					self.emit_addr(disp=disp, pc=pc)
					return 4 | STEP_OVER | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o in (0x3600, 0x3601):
				# TBIT imm, reg only exists as a word operation
				stream.push("tbit    ")
				if ((opcode & 0x001f) == 0x0011):
					imm = self.format_medium_imm_decimal(stream, opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
				else:
					imm = self.format_short_imm_decimal(stream, opcode & 0x001f)
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
					return 2 | SUPPORTED
			
			elif o in (0x4000, 0x4200, 0x4400, 0x4600,	0x4800, 0x4a00, 0x4c00, 0x4e00,	0x5000, 0x5200, 0x5400, 0x5600,	0x5800, 0x5a00, 0x5c00, 0x5e00):
				# Conditional or unconditional branch with 9-bit displacement
				if ((opcode & 0x01e0) != 0x01e0):
					addr = (opcode & 0x1e00) >> 4 | (opcode & 0x001e)
					if ((opcode & 0x01e0) == 0x01c0):
						stream.push("br      ")
						disp = self.format_pc_disp9(stream, pc, addr)
						self.emit_addr(disp=disp, pc=pc)
						stream.push('\n')	# new line for "end of block"
					else:
						stream.format("b%s     ", self.s_cc[(opcode & 0x01e0) >> 5])
						disp = self.format_pc_disp9(stream, pc, addr)
						self.emit_addr(disp=disp, pc=pc)
				else:
					stream.push("res")
				return 2 | SUPPORTED
			
			elif o in (0x4001, 0x6001):
				stream.format("add%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x4201, 0x6201):
				stream.format("addu%c   ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x4601, 0x6601):
				stream.format("mul%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x4801, 0x6801):
				stream.format("ashu%c   ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x4a01, 0x6a01):
				stream.format("lsh%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x4c01, 0x6c01):
				stream.format("xor%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x4e01, 0x6e01):
				stream.format("cmp%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x5001, 0x7001):
				stream.format("and%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x5201, 0x7201):
				stream.format("addc%c   ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o == 0x5401:
				if (not (opcode & 0x01e0) == 0x01e0):
					r = (opcode & 0x001e) >> 1
					if ((opcode & 0x01e0) == 0x01c0):
						stream.push("jump    ")
						self.format_reg(stream, r)
						stream.push('\n')	# new line for "end of block"
					else:
						stream.format("j%s     ", self.s_cc[(opcode & 0x01e0) >> 5])
						self.format_reg(stream, r)
					return 2 | (STEP_OUT if (opcode == 0x55dd) else 0) | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o in (0x5801, 0x7801):
				stream.format("mov%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x5a01, 0x7a01):
				stream.format("subc%c   ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x5c01, 0x7c01):
				stream.format("or%c     ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x5e01, 0x7e01):
				stream.format("sub%c    ", 'w' if BIT(opcode, 13) else 'b')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o == 0x6000:
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
				else:
					stream.push("mulsb   ")
					self.format_reg(stream, (opcode & 0x001e) >> 1)
					stream.push(", ")
					self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o == 0x6200:
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
				else:
					stream.push("mulsw   ")
					self.format_reg(stream, (opcode & 0x001e) >> 1)
					stream.push(", ")
					self.format_rpair(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o in (0x6400, 0x6600):
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
					return 2 | SUPPORTED
				else:
					stream.push("movd    ")
					imm = self.format_imm21(stream, u32(opcode & 0x0200) << 11 | u32(opcode & 0x000e) << 16 | u32(opcode & 0x0010) << 12 | opcodes.r16(pc + 2))
					self.emit_addr(imm=imm, pc=pc)
					stream.push(", ")
					self.format_rpair(stream, (opcode & 0x01e0) >> 5)
					return 4 | SUPPORTED
			
			elif o in (0x6800, 0x6a00):
				stream.format("mov%cb   ", 'z' if BIT(opcode, 9) else 'x')
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o == 0x6c00:
				# Push and pop group
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
				else:
					if (BIT(opcode, 8)):
						stream.push("popret  ")
					elif (BIT(opcode, 7)):
						stream.push("pop     ")
					else:
						stream.push("push    ")
					stream.format("$%d, ", ((opcode & 0x0060) >> 5) + 1)
					self.format_reg(stream, (opcode & 0x001e) >> 1)
					if (BIT(opcode, 8)):
						stream.format(" ; %cMM", 'L' if BIT(opcode, 7) else 'S')
						stream.push('\n')	# new line for "end of block"
						return 2 | STEP_OUT | SUPPORTED
				return 2 | SUPPORTED
			
			elif o == 0x6e00:
				if (not (opcode & 0x01c0) == 0x01c0):
					stream.format("s%s     ", self.s_cc[(opcode & 0x01e0) >> 5])
					self.format_reg(stream, (opcode & 0x001e) >> 1)
				else:
					stream.push("res")
				return 2 | SUPPORTED
			
			elif o == 0x7000:
				stream.push("lpr     ")
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_rproc(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o == 0x7200:
				stream.push("spr     ")
				self.format_rproc(stream, (opcode & 0x01e0) >> 5)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				return 2 | SUPPORTED
			
			elif o == 0x7400:
				# Conditional or unconditional branch to large address
				if (not (opcode & 0x01e0) == 0x01e0) and (self.m_arch != ARCH_CR16A):
					addr = u32(opcode & 0x000e) << 16 | u32(opcode & 0x0010) << 12 | opcodes.r16(pc + 2)
					if ((opcode & 0x01e0) == 0x01c0):
						stream.push("br      ")
						disp = self.format_pc_disp21(stream, pc, addr)
						self.emit_addr(disp=disp, pc=pc)
						stream.push('\n')	# new line for "end of block"
					else:
						stream.format("b%s     ", self.s_cc[(opcode & 0x01e0) >> 5])
						disp = self.format_pc_disp21(stream, pc, addr)
						self.emit_addr(disp=disp, pc=pc)
					return 4 | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o == 0x7401:
				# Jump and link to small address
				stream.push("jal     ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				return 2 | SUPPORTED
			
			elif o == 0x7600:
				# Branch and link to large address
				if (self.m_arch == ARCH_CR16A):
					stream.push("res")
					return 2 | SUPPORTED
				else:
					stream.push("bal     ")
					self.format_rpair(stream, (opcode & 0x01e0) >> 5)
					stream.push(", ")
					disp = self.format_pc_disp21(stream, pc, u32(opcode & 0x000e) << 16 | u32(opcode & 0x0010) << 12 | opcodes.r16(pc + 2))
					self.emit_addr(disp=disp, pc=pc)
					return 4 | STEP_OVER | SUPPORTED
			
			elif o == 0x7601:
				# TBIT reg, reg only exists as a word operation
				stream.push("tbit    ")
				self.format_reg(stream, (opcode & 0x001e) >> 1)
				stream.push(", ")
				self.format_reg(stream, (opcode & 0x01e0) >> 5)
				return 2 | SUPPORTED
			
			elif o == 0x7800:
				if (opcode == 0x79fe):
					stream.push("retx")
					return 2 | STEP_OUT | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o == 0x7a00:
				if ((opcode & 0x01e0) == 0x01e0):
					stream.push("excp    ")
					self.format_excp_vector(stream, (opcode & 0x001e) >> 1)
					return 2 | STEP_OVER | SUPPORTED
				else:
					stream.push("res")
					return 2 | SUPPORTED
			
			elif o == 0x7c00:
				if (opcode == 0x7dde):
					stream.push("di")
				elif (opcode == 0x7dfe):
					stream.push("ei")
				else:
					stream.push("res")
				return 2 | SUPPORTED
			
			elif o == 0x7e00:
				# Various special operations
				if (opcode == 0x7ffe):
					stream.push("wait")
				elif (self.m_arch == ARCH_CR16A):
					stream.push("res")
				elif ((opcode & 0x000c) == 0x0000):
					stream.push("muluw   ")
					self.format_reg(stream, (opcode & 0x0012) >> 1)
					stream.push(", ")
					self.format_rpair(stream, (opcode & 0x01e0) >> 5)
				elif ((opcode & 0x011e) == 0x0004):
					if (BIT(opcode, 7)):
						stream.push("storm   ")
					else:
						stream.push("loadm   ")
					stream.format("$%d", ((opcode & 0x0060) >> 5) + 1)
				elif (opcode == 0x7fe6):
					stream.push("eiwait")
				else:
					stream.push("res")
				return 2 | SUPPORTED
			
			else:
				stream.push("res")
				return 2 | SUPPORTED
	# end of disassemble


class CR16A_Disassembler(CR16B_Disassembler):
	"""CR16B is the real implementation, this just sets the CR16A arch"""
	def __init__(self):
		CR16B_Disassembler.__init__(self, arch=ARCH_CR16A)
	
	def format_rproc(self, stream, reg):	# u8 reg
		if reg == 1: stream.push("psr")
		elif reg == 3: stream.push("intbase")
		elif reg == 11: stream.push("isp")
		else:
			stream.push("res")

def put(t):
	print(t)


if __name__ == '__main__':
	
	SHOW_ADDRESS = True
	SHOW_BYTES = True
	SHOW_WORDS = True
	SHOW_ASM = True
	ADDRESS_START = 0x200	#0x040000
	ADDRESS_STOP = ADDRESS_START + 0x010000
	
	import sys
	
	"""
	import argparse
	argp = argparse.ArgumentParser(description='Disassemble binary into CR16B assembly')
	
	# Add the arguments
	#argp.add_argument('--input', nargs='+', action='append', type=str, required=True, help='input file(s)')
	#argp.add_argument('--output', nargs='?', action='store', type=str, help='output file')
	argp.add_argument(dest='input', nargs='1', action='append', type=str, help='input filename')
	
	# Execute the parse_args() method
	args = argp.parse_args()
	
	input_filename = args.input
	"""
	
	if len(sys.argv) < 2:
		
		ROM_FILENAME = 'CART_GL8008CX_Update.dump.000.seg1-64KB__4KB_used.bin'
		ADDRESS_START = 0x0
		ADDRESS_STOP = ADDRESS_START + 0x01000
		#ROM_FILENAME = 'test_in.hex'
		#ROM_FILENAME = 'test_all.hex'
	else:
		ROM_FILENAME = sys.argv[1]
	
	
	put('Disassembling "%s"...' % ROM_FILENAME)
	
	if ROM_FILENAME.endswith('.hex'):
		# Load hex
		data = []
		for l in open(ROM_FILENAME, 'r'):
			v16 = int(l, 16)
			data.append(v16 & 0xff)
			data.append(v16 >> 8)
		data = bytes(data)
		#put(data)
		opcodes = DataBuffer(data)
	else:
		# Load binary image
		with open(ROM_FILENAME, 'rb') as h:
			data = h.read()
			opcodes = DataBuffer(data)
	
	# Instantiate
	#dasm = CR16A_Disassembler()
	dasm = CR16B_Disassembler()
	
	# Go!
	stream = Stream()
	
	pc = ADDRESS_START
	while pc < ADDRESS_STOP:
		
		r = dasm.disassemble(stream, pc, opcodes)
		
		#put('r = 0x%04X' % r)
		if not (r & SUPPORTED):
			put('NOT SUPPORTED! Quitting...')
			break
		
		l = r & LENGTHMASK	# Number of bytes consumed
		
		# Dump as 16bit words
		t_raw16 = ' '.join([ '%04X' % opcodes.r16(pc+pci*2) for pci in range(l//2)  ])
		# Dump as 8bit bytes
		t_raw8 = ' '.join([ '%02X' % opcodes.r8(pc+pci) for pci in range(l)  ])
		
		t = stream.dump()
		#put('%06X:	%s	|	%s' % (pc, t_raw.ljust(11), t))
		#put('%06X:	%s	|	%s	|	%s' % (pc, t_raw8.ljust(11), t_raw16.ljust(9), t))
		
		r = ''
		if SHOW_ADDRESS: r += '%06X:	'% pc
		if SHOW_BYTES: r += '%s	' % t_raw8.ljust(11)
		if SHOW_WORDS: r += '%s	' % t_raw16.ljust(9)
		if SHOW_ASM: r += '%s' % t
		put(r)
		
		# Increment program counter
		pc += l
		if (pc >= len(data)):
			put('End of data!')
			break
	
	
	# Address usage statistics
	put('-'*40)
	put('Addresses:')
	for addr, uses in sorted(dasm.addrs_found.items()):
		#uses = dasm.addrs_found[addr]
		if addr in KNOWN_ADDRS:
			addr_str = KNOWN_ADDRS[addr]
		else:
			
			# Filter single-use unknown addresses
			#if len(uses) == 1: continue
			
			addr_str = '0x%06X' % addr
			
		put('	%s: Used by %s' % (addr_str, ', '.join([ '0x%06X'%u for u in uses ])))
		#put('	0x%06X: Used by %s' % (addr, ', '.join([ '0x%06X'%u for u in uses ])))
	
	put('End.')