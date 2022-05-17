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
		self.line_num = 0
	
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
		self.line_num = 0
		self.parse_root()
	
	def get_next_line(self, strip=True):
		if self.line_num >= len(self.lines):
			self.put('End of file!')
			return None
		
		line = self.lines[self.line_num]
		self.line_num += 1
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
				params_text = rest_text[rest_text.index('(')+1:rest_text.index(')')]
				params = parse_params_text(params_text)
				self.parse_block(name=name, params=params)
			
		
	def parse_block(self, name, params):
		# New function "define dso_local void @put(i8* %0) #0 {"
		self.put('Parsing block "%s"...' % name)
		
		params_count = len(params)
		start_line_num = self.line_num
		
		self.emit('; Function "%s", %d parameter(s)' % (name, params_count))
		self.emit('%s:' % name)
		
		# Step 1: Pre-process, count number of assignments
		assignments = params
		while True:
			line = self.get_next_line()
			if line is None: break
			if line == '': continue
			if line == '}': break
			#self.put_debug('parse_block: %s' % line)
			
			words = line.split(' ')
			
			if words[0][-1:] == ':':
				#self.put_debug('Label')
				pass
			elif (len(words) > 2) and (words[1] == '='):
				#self.put('Assignment')
				name = words[0]
				if not name in assignments:
					assignments[name] = ' '.join(words[2:])
			#else:
			#	self.put('Unhandled: %s' % line)
		
		put('Assignments found: %s' % str(assignments))
		aks = []
		for a in assignments:
			aks.append(a)
		
		self.emit('; Uses %d local assignment(s)' % (len(assignments) - params_count))
		
		# Emit function preamble
		#self.emit('push    $2, era\n')
		
		# Make space on stack
		self.emit('	addw	$-%d,sp' % ((len(assignments) - params_count) * 2))
		
		# Copy parameters to local assignments
		#for i in range(params_count):
		#	self.emit('	storw	r%d,0(sp)' % (2+i))
		
		# Step 2: Parse instructions
		self.line_num = start_line_num
		while True:
			line = self.get_next_line()
			if line is None: break
			if line == '': continue
			if line == '}': break
			
			self.put_debug('parse_block:	%d	%s' % (self.line_num, line))
			# Show commented LLVM IR in S file
			#self.emit('; %d	%s' % (self.line_num, line))
			
			words = line.split(' ')
			
			if words[0][-1:] == ':':
				#self.put_debug('Label')
				self.emit('label_%s:' % words[0][:-1])
			
			elif (len(words) > 2) and (words[1] == '='):
				#self.put('Assignment')
				name = words[0]
				
				# Ignore "alloca" for now
				if words[2] == 'alloca':
					continue
				
				elif words[2] == 'load':
					dst_name = words[0]
					dst_i = aks.index(dst_name)
					
					addr_name = words[5].replace(',', '')
					addr_i = aks.index(addr_name)
					self.emit('	loadw %d(sp), r0' % ((addr_i - params_count) * 2))
					self.emit('	storw r0, %d(sp)' % ((dst_i - params_count) * 2))
				else:
					put('UNSUPPORTED, YET: %s' % line)
			
			elif words[0] == 'store':
				dst_name = words[4].replace(',', '')
				dst_i = aks.index(dst_name)
				
				src_name = words[2].replace(',', '')
				if (not src_name in aks):
					# Immediate!
					imm = int(src_name)
					self.emit('	movw $%d, %d(sp)' % (imm, (dst_i - params_count) * 2))
				else:
					src_i = aks.index(src_name)
					if src_i <= params_count:
						self.emit('	storw r%d, %d(sp)' % (2+src_i, (dst_i - params_count) * 2))
					else:
						self.emit('	loadw %d(sp), r0' % ((src_i - params_count) * 2))
						self.emit('	storw r0, %d(sp)' % ((dst_i - params_count) * 2))
			
			elif words[0] == 'ret':
				
				#@TODO: Make sure to set a return value!
				self.emit('	;@TODO: Return something?')
				
				# Fix stack
				self.emit('	subw	$-%d,sp' % ((len(assignments) - params_count)*2))
				self.emit('	jump	(ra,era)')
			else:
				self.put('Unhandled: %s' % line)
		
		# Emit function epilogue
		self.emit('; End of function\n\n')


if __name__ == '__main__':
	filename = 'foo.c'
	
	cc = CR16B_Compiler()
	cc.compile(filename)