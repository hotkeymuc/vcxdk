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

def parse_type(type_text):
	r = type_text
	return r

def parse_params_text(params_text):
	words = params_text.split(',')
	r = OrderedDict()
	for w in words:
		ws = w.strip().split(' ')
		type_text = ' '.join(ws[:-1])
		name = ws[-1]
		r[name] = parse_type(type_text)
	return r

class CR16B_Compiler:
	def __init__(self):
		self.is_in_function = False
	
	def put(self, text):
		put(text)
	
	def compile(self, filename):
		filename_ll = filename[:filename.rindex('.')] + '.ll'
		# Clean
		if os.path.isfile(filename_ll):
			self.put('Cleaning LLVM file "%s"...' % filename_ll)
			os.remove(filename_ll)
		
		self.put('Compiling "%s" to LLVM "%s"...' % (filename, filename_ll))
		r = os.system('clang -S -emit-llvm %s' % filename)
		put('r=%s' % str(r))
		
		if not os.path.isfile(filename_ll):
			raise ParseErrror('LLVM file "%s" was not created!' % filename_ll)
		
		
		self.put('Loading LLVM file "%s"...' % filename_ll)
		with open(filename_ll, 'r') as h:
			data = h.read()
		
		#put('File contents:')
		#put(data)
		self.parse(data)
	
	def enter_function(self, name, params):
		if self.is_in_function:
			raise Error('Start of function, but still inside one!')
		self.is_in_function = True
		
		#@TODO: Remember the parameters / map to registers
		
	
	def parse(self, text):
		i = 0
		for line in text.split('\n'):
			i += 1
			self.put('%d:	%s' % (i, line))
			
			# Strip comments
			if ';' in line: line = line[:line.index(';')]
			
			line = line.strip()
			
			# Skip empty lines
			if line == '': continue
			
			words = line.split(' ')
			# Early ignore of some meta stuff
			if words[0] == 'source_filename': continue
			if words[0] == 'target': continue
			
			self.put('%s' % line)
			
			if words[0] == 'define':
				# New function "define dso_local void @put(i8* %0) #0 {"
				ret_type_text = words[2]
				ret_type = parse_type(ret_type_text)
				rest_text = ' '.join(words[3:])
				name = rest_text[:rest_text.index('(')]
				params_text = rest_text[rest_text.index('(')+1:rest_text.index(')')]
				params = parse_params_text(params_text)
				self.enter_function(name=name, params=params_text)
			
			if words[0] == '}':
				if not self.is_in_function:
					raise Error('End of function without being in one!')
				self.is_in_function = False
			

if __name__ == '__main__':
	filename = 'foo.c'
	
	cc = CR16B_Compiler()
	cc.compile(filename)