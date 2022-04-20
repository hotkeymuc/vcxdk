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


class CR16B_Assembler:
	def __init__(self):
		self.stor = DataStore()
		self.pc = 0x0000
	
	def w(self, v):
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
		put(' '.join(['%02X'%b for b in self.stor.get_data()]))
	
	def assemble_bal(self, dest, lnk_pair=13, pc=None):
		"""lnk_pair: 13 = 0b1101 = ra,era"""
		
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
	
	def assemble_movd(self, imm21, dest_pair):
		"""
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
	
	def assemble_br(self, disp, cond=0):
		"""cond: 1=NE"""
		
		if (disp >= 0b1000000000):
			raise ValueError('displacement too big for short br')
		
		self.w16(
			  (0b010 << 13)\
			| (((disp & 0b111100000) >> 5) << 9)\
			| (cond << 5)\
			| ((disp & 0b000011111))
		)
		
	def assemble_bne(self, disp):
		#self.w16(0x4020 + disp)
		self.assemble_br(cond=1, disp=disp)
		
	
	def assemble_basic_reg_reg(self, i, op, src_reg, dest_reg):
		
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
	



if __name__ == '__main__':
	
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
	
	asm.pc = 0x200
	
	asm.w([0xf1, 0x39, 0x00, 0xb7])	# movw    $0xB700, sp
	asm.w([0x20, 0x6c])	# push    $2, r0
	
	asm.assemble_movd(0x189E91, 4)	# movd    $0x189E91, (r5,r4)
	asm.assemble_movd(0x18AB57, 2)	# movd    $0x18AB57, (r3,r2)
	asm.assemble_bal(0x1805c4)	# bal     (ra,era), 0x1805c4
	
	asm.w([0xe4,0x23])	# adduw   $0x4, sp
	asm.w([0x01, 0x0e])	# cmpb    $0x1, r0
	
	asm.assemble_bne(disp=0x16)
	
	asm.dump()