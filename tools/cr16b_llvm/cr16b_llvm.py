#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""

There is no open source version of a CR16B compiler, yet. (There is only the proprietary CR16 Toolset for Windows)

Idea:
	* Create LLVM IR code (e.g. via clang)
		clang -S -emit-llvm foo.c
		clang -cc1 foo.c -emit-llvm
	* Transform IR instructions into CR16B assembly
	* Compile/link using cr16b_asm.py

Tricky:
	Convert assignments ("%0", "%1", "%2", ...) into registers/stack



"""
import os
from collections import OrderedDict

def put(t):
	print(t)
def put_debug(t):
	print(t)

def parse_type(type_text):
	r = type_text
	return r

def parse_params_text(params_text):
	words = params_text.split(',')
	r = OrderedDict()
	for w in words:
		w = w.strip()
		if w == '': continue
		ws = w.split(' ')
		type_text = ' '.join(ws[:-1])
		name = ws[-1]
		r[name] = parse_type(type_text)
	return r

class CR16B_Compiler:
	def __init__(self):
		self.lines = []
		self.line_num = -1
	
	def put(self, text):
		put(text)
	def put_debug(self, text):
		put_debug(text)
	
	def emit(self, t):
		put('>>> %s' % str(t))
	
	def compile(self, filename):
		filename_ll = filename[:filename.rindex('.')] + '.ll'
		# Clean
		if os.path.isfile(filename_ll):
			self.put('Cleaning LLVM file "%s"...' % filename_ll)
			os.remove(filename_ll)
		
		self.put('Compiling "%s" to LLVM "%s"...' % (filename, filename_ll))
		r = os.system('clang -S -emit-llvm %s' % filename)
		#put('clang result=%s' % str(r))
		
		if r != 0:
			raise Error('Compilation using clang failed. r=%s' % str(r))
		
		if not os.path.isfile(filename_ll):
			raise ParseErrror('LLVM file "%s" was not created!' % filename_ll)
		
		
		self.put('Loading LLVM file "%s"...' % filename_ll)
		with open(filename_ll, 'r') as h:
			data = h.read()
		
		self.lines = data.split('\n')
		self.line_num = -1
		self.parse_root()
	
	def get_next_line(self, strip=True):
		self.line_num += 1
		if self.line_num >= len(self.lines):
			self.put('End of file!')
			return None
		line = self.lines[self.line_num]
		
		#self.put('%d:	%s' % (self.line_num, line))
		
		if strip:
			# Strip comments
			if ';' in line: line = line[:line.index(';')]
			
			# Compress
			line = line.strip()
		
		return line
	
	def parse_root(self):
		while True:
			line = self.get_next_line()
			line_i = self.line_num
			if line is None: break
			if line == '': continue
			
			words = line.split(' ')
			# Early ignore of some meta stuff
			if words[0] == 'source_filename': continue
			if words[0] == 'target': continue
			
			#self.put_debug('parse_root: %s' % line)
			
			if words[0] == 'define':
				ret_type_text = words[2]
				ret_type = parse_type(ret_type_text)
				rest_text = ' '.join(words[3:])
				
				name = rest_text[:rest_text.index('(')]
				#name = '_function_%s' % (name.replace('%', ''))
				if name.startswith('@'):
					name = name[1:]
				
				params_text = rest_text[rest_text.index('(')+1:rest_text.index(')')]
				params_texts = parse_params_text(params_text)
				params = OrderedDict()
				for i, param_id in enumerate(params_texts.keys()):
					params[param_id] = {
						'id': param_id,
						'register': 'r%d' % (2+i),
						'first_read': None,
						'last_read': None,
						'first_write': line_i,
						'last_write': line_i,
						'text': params_texts[param_id],
					}
				self.parse_block(def_name=name, params=params)
			
		
	def parse_block(self, def_name, params):
		# New function "define dso_local void @put(i8* %0) #0 {"
		self.put('Parsing block "%s"...' % def_name)
		
		params_count = len(params)
		start_line_num = self.line_num
		
		self.emit('; Function "%s"' % def_name)
		self.emit('; Uses %d parameter(s):' % params_count)
		for id, param in params.items():
			self.emit(';	* %s in %s' % (param['id'], param['register']))
		
		
		# State
		assignments = params
		labels = {}
		heap_size = 0
		register_use = {}
		for i in range(14):
			reg_name = 'r%d' % i
			register_use[reg_name] = False
		
		# Parameters are blocking r2...
		for i in range(params_count):
			register_use['r%d' % (2+i)] = True
		# r0 is our scratch register and should never be free to use
		register_use['r0'] = True
		
		
		# Step 1: Pre-process, count number of assignments
		while True:
			line = self.get_next_line()
			line_i = self.line_num
			if line is None: break
			if line == '': continue
			if line == '}': break
			#self.put_debug('parse_block: pre-processing:	%d	%s' % (line_i, line))
			
			words = line.split(' ')
			
			if words[0][-1:] == ':':
				#self.put_debug('Label')
				labels[words[0][:-1]] = line_i
			
			elif (len(words) > 2) and (words[1] == '='):
				#self.put('Assignment')
				dst_name = words[0]
				
				if dst_name in assignments:
					# Known assignment
					if assignments[dst_name]['first_write'] is None:
						assignments[dst_name]['first_write'] = line_i
					assignments[dst_name]['last_write'] = line_i
				else:
					# New assignment
					
					reg = None	# register is allocated just-in-time
					type_text = ' '.join(words[2:])
					type_size = None
					
					assignments[dst_name] = {
						'id': dst_name,
						'register': reg,
						'type_text': type_text,
						'type_size': type_size,
						'first_read': None,
						'last_read': None,
						'first_write': line_i,
						'last_write': line_i,
						
					}
				
				if words[2] == 'alloca':
					#@TODO: Actually reserve some memory on heap
					#@FIXME: Think about how to actually store the data...
					type_text = words[3].replace(',','')
					if type_text == 'i8*': type_size = 1
					elif type_text == 'i16*': type_size = 2
					elif type_text == 'i32*': type_size = 4
					elif type_text == 'i8': type_size = 1
					elif type_text == 'i16': type_size = 2
					elif type_text == 'i32': type_size = 4
					else:
						self.put('Unknown type "%s" - cannot guess size!' % type_text)
						type_size = 2
					
					# Remember an address on heap
					assignments[dst_name]['register'] = heap_size
					assignments[dst_name]['type_text'] = type_text
					assignments[dst_name]['type_size'] = type_size
					
					heap_size += type_size
					pass
					
				elif words[2] == 'load':
					addr_name = words[5].replace(',', '')
					if assignments[addr_name]['first_read'] is None:
						assignments[addr_name]['first_read'] = line_i
					assignments[addr_name]['last_read'] = line_i
				else:
					
					#@TODO: Handle other operations (icmp, mul, ...)
					put('UNSUPPORTED FOR ASSIGNMENT STATISTICS, YET: %s' % line)
					
			
			elif words[0] == 'store':
				src_name = words[2].replace(',', '')
				if (src_name in assignments):
					if assignments[src_name]['first_read'] is None:
						assignments[src_name]['first_read'] = line_i
					assignments[src_name]['last_read'] = line_i
				
				dst_name = words[4].replace(',', '')
				if assignments[dst_name]['first_write'] is None:
					assignments[dst_name]['first_write'] = line_i
				assignments[dst_name]['last_write'] = line_i
				
			elif words[0] == 'call':
				rest_text = ' '.join(words[2:])
				
				call_name = rest_text[:rest_text.index('(')]
				args_text = rest_text[rest_text.index('(')+1:rest_text.rindex(')')]
				#args = parse_params_text(args_text)
				
				#@TODO: Parse call arguments!
				self.put('@TODO: Call "%s" with args "%s"' % (call_name, args_text))
				# Update use of parameters
				# Maybe even pre-select registers?
				
			
			#else:
			#	self.put('Unhandled: %s' % line)
		
		#put('Assignments found: %s' % str(assignments))
		self.put('Assignments:')
		a_ids = []
		for a_id, assignment in assignments.items():
			a_ids.append(a_id)
			self.put('	* %s: %s' % (a_id, str(assignment)))
		
		
		self.emit('; Uses %d local assignment(s) excl. params' % (len(assignments) - params_count))
		self.emit('; Uses %d byte(s) of heap' % heap_size)
		
		
		# Emit function preamble
		self.emit('_%s:' % def_name)
		
		#self.emit('push    $2, era\n')
		
		# Make space on stack
		#self.emit('	addw	$-%d,sp' % ((len(assignments) - params_count) * 2))
		self.emit('	addw	$-%d,sp' % heap_size)
		
		# Copy parameters to local assignments
		#for i in range(params_count):
		#	self.emit('	storw	r%d,0(sp)' % (2+i))
		
		
		# Step 2: Parse instructions
		self.line_num = start_line_num
		line_i = self.line_num
		while True:
			# Check if we can free some registers
			for a_id, assignment in assignments.items():
				last_use = None
				if (assignment['last_write'] is not None):
					last_use = assignment['last_write']
				if (assignment['last_read'] is not None):
					if last_use is None:
						last_use = assignment['last_read']
					else:
						last_use = max(last_use, assignment['last_read'])
				if last_use == line_i:
					reg_name = assignment['register']
					#self.put_debug('Can free up %s (%s)' % (a_id, reg_name)))
					if reg_name in register_use:
						self.put_debug('Freeing up %s (%s)' % (a_id, reg_name))
						#assignment['register'] = None
						register_use[reg_name] = False
				
			
			line = self.get_next_line()
			line_i = self.line_num
			if line is None: break
			if line == '': continue
			if line == '}': break
			
			
			# Check which registers are used for the first time
			for a_id, assignment in assignments.items():
				if assignment['first_write'] == line_i:
					#self.put_debug('Need to allocate a register for writing to %s' % a_id)
					
					found = False
					for reg_name, reg_used in register_use.items():
						if not reg_used:
							register_use[reg_name] = True
							assignment['register'] = reg_name
							self.put_debug('Allocated register %s for storing %s' % (reg_name, a_id))
							found = True
							break
					if not found:
						raise Error('Ran out of free registers!')
			
			self.put_debug('parse_block:	%d	%s' % (self.line_num, line))
			# Show commented LLVM IR in S file
			#self.emit('; %d	%s' % (self.line_num, line))
			
			
			words = line.split(' ')
			
			if words[0][-1:] == ':':
				#self.put_debug('Label')
				self.emit('_%s_%s:' % (def_name, words[0][:-1]))
			
			elif (len(words) > 2) and (words[1] == '='):
				#self.put('Assignment')
				dst_name = words[0]
				
				# Ignore "alloca" for now
				if words[2] == 'alloca':
					#@TODO: Actually reserve some memory on heap
					continue
				
				elif words[2] == 'load':
					addr_name = words[5].replace(',', '')
					
					#dst_i = a_ids.index(dst_name)
					#addr_i = a_ids.index(addr_name)
					#self.emit('	loadw %d(sp), r0' % ((addr_i - params_count) * 2))
					#self.emit('	storw r0, %d(sp)' % ((dst_i - params_count) * 2))
					dst_reg = assignments[dst_name]['register']
					addr_reg = assignments[addr_name]['register']
					if (type(addr_reg) is int):
						if (type(dst_reg) is int):
							# from mem to mem
							self.emit('	loadw %d(sp), %s' % (addr_reg, 'r0'))
							self.emit('	storw %s, %d(sp)' % ('r0', dst_reg))
						else:
							# from mem to reg
							self.emit('	loadw %d(sp), %s' % (addr_reg, dst_reg))
					else:
						if (type(dst_reg) is int):
							# from reg to mem
							self.emit('	loadw %s, %s' % (addr_reg, 'r0'))
							self.emit('	storw %s, %d(sp)' % ('r0', dst_reg))
						else:
							# from reg to reg
							self.emit('	loadw %s, %s' % (addr_reg, dst_reg))
					
				else:
					put('UNSUPPORTED, YET: %s' % line)
			
			elif words[0] == 'store':
				src_name = words[2].replace(',', '')
				dst_name = words[4].replace(',', '')
				
				dst_reg = assignments[dst_name]['register']
				if (not src_name in a_ids):
					# Immediate!
					imm = int(src_name)
					
					if (type(dst_reg) is int):
						# from imm to mem
						self.emit('	storw $%d, %d(sp)' % (imm, dst_reg))
					else:
						# from imm to reg
						self.emit('	movw $%d, %s' % (imm, dst_reg))
				else:
					# from assign...
					src_reg = assignments[src_name]['register']
					
					if (type(src_reg) is int):
						if (type(dst_reg) is int):
							# from mem to mem
							self.emit('	loadw %d(sp), %s' % (src_reg, 'r0'))
							self.emit('	storw %s, %d(sp)' % ('r0', dst_reg))
						else:
							# from mem to reg
							self.emit('	loadw %d(sp), %s' % (src_reg, dst_reg))
					else:
						if (type(dst_reg) is int):
							# from reg to mem
							self.emit('	storw %s, %d(sp)' % (src_reg, dst_reg))
						else:
							# from reg to reg
							self.emit('	movw %s, %s' % (src_reg, dst_reg))
					
			
			elif words[0] == 'ret':
				
				if words[1] != 'void':
					#@TODO: Make sure to set a return value!
					self.put('Returning a value is not yet implemented! ... I know!')
					self.emit('	;@TODO: Return "%s"!' % (' '.join(words[1:])))
					#self.emit('	movw %s, %s' % (r0, dst_reg))
				
				# Fix stack
				#self.emit('	subw	$-%d,sp' % ((len(assignments) - params_count)*2))
				self.emit('	subw	$-%d,sp' % heap_size)
				self.emit('	jump	(ra,era)')
			else:
				self.put('Unhandled: %s' % line)
		
		# Emit function epilogue
		self.emit('; End of function\n\n')


if __name__ == '__main__':
	filename = 'foo.c'
	
	cc = CR16B_Compiler()
	cc.compile(filename)