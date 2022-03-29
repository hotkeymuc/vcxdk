#!/usr/bin/python
# -*- coding: utf-8 -*-
"""

V-Tech CX BusIO Client
(based on the old VTech Interceptor)

Communicates wo an Arduino running the VTechCXBusIO.ino sketch.
This program can be used to visualize real-time bus activity, read ROMs and write to RAM cartridges.

Keys:
	SPACE	Start
				SPACE	Toggle fadeout / one-shot
	TAB	Jump from bank to bank
	BACKSPC	Clear screen
	d	Dump current address and following
	s	Save memory dump to dump/[timestamp]
	1	Toggle "ignore < 0x1000"
	i/u	Add current address to IGNORE_LIST / un-ignore
	w/q	Add current address to WATCH_LIST / quit watching
	t	toggle traffic display
	s	Save memory dump
	
	

Problem with Arduino DUE:
	Runs at native USB speed (480M) but may effectively run very slow...
	Internet says: It depends on how often you *POLL* the USB port.
	So: For DUE we should not call "serial.read" too often in order to gain maximum speed.

"""
import serial
import time
import math
import random
#import struct
import numpy

import pygame
from pygame.locals import *

def put(t):
	print(str(t))


VERSION = 'VTech GLCX BusIO Client'

SERIAL_PORT = '/dev/ttyACM0'	# Due native
#SERIAL_PORT = '/dev/ttyACM1'	# Due native

#SERIAL_BAUD = 4000000	# F*** yeah 4MBit on MEGA 2560. On DUE this is ignored (uses native USB speed)
SERIAL_BAUD = 2000000
#SERIAL_BAUD = 115200

COMMAND_LATENCY = 0.1	# Wait for the command to be processed before polling its result
LINE_LATENCY = 0.001	# Throttle A LITTLE before polling a line

DUMMY_ACTIVITY = not True	# Produce some random data to test the parser

#MEMORY_SIZE = 0x080000	#0x100000	#0x200000	#0x40000	# CX: 2MB = 0x200000 = 2097152
MEMORY_SIZE = 0x100000	#0x40000	# CX: 2MB = 0x200000 = 2097152
#MEMORY_SIZE = 0x080000
BANK_SIZE = 512*1024

RECORD_COMBOS = False
ZOOM = 1	#2
PADDING = 16
BANK_WIDTH = 1024	#512	#256	#320
BANK_HEIGHT = BANK_SIZE // BANK_WIDTH
BANKS_X = 1
BANKS_Y = 2
SCREEN_SIZE = (BANK_WIDTH*ZOOM*BANKS_X + PADDING*(1+BANKS_X), (BANK_HEIGHT + 1)*ZOOM*BANKS_Y + PADDING*(1+BANKS_Y))

# Default start address
ADDR_START = 0x000000

#EDGE_FALLING = 0
#EDGE_RISING = 1
#EDGE_CHANGE = 2
#EDGE_HIGH = 3

HIGH = 1
LOW = 0


# Binary protocol
BUFFER_SIZE = 8192
BUFFER_SIZE_MIN_FLUSH = 2048
PACKET_SIZE = 6	# addr_hi, addr_lo, data, flags_hi, flags_lo, checksum

# HEX protocol:Traffic: 61138 Bps	6213 steps

KEY_RETRIG_DELAY = 20
KEY_RETRIG_DELAY2 = 1

PAGE_STEP = 16	#*8

# Bus addresses to watch out for
# Some very important addresses to watch (for STDIN/OUT)
# How to find them: Do a thing for X times (e.g. 100 times). Dump the "combos by count", then look for address accesses that happened AROUND the same number of times (some events get lost!). Then: put addr candidates to watch list and see in real time if something happens
WATCH_LIST = [
	# 0xfd00	Put interesting GLCX ports here! (serial / LED, keyboard, ...)
]

IGNORE_LIST = [
	"""
	0x143C,	#(busData == 0xF2): continue	# happens a lot - ignore
	"""
]


def to_bin(v, l):
	return bin(v)[2:].zfill(l)

def to_hexdump(data, ofs=0, count=0x100, addr_ofs=0):
	r = ''
	
	col = 8
	width = 16
	o = ofs
	e = min(len(data), ofs+count)
	y = 0
	while (o < e):
		
		if (y > 0):
			r += '\n'
		
		# Addr
		a = o + addr_ofs
		r += '%06X\t' % (a)
		
		# Hex
		x = 0
		o2 = o
		while (x < width) and (o2 < e):
			if (x > 0) and (x % col) == 0: r += ' '
			r += '%02x ' % data[o2]
			
			o2 += 1
			x += 1
		while (x < width):
			if (x > 0) and (x % col) == 0: r += ' '
			r += '   '
			x += 1
		
		r += '\t'
		
		# Bin
		x = 0
		o2 = o
		while (x < width) and (o2 < e):
			if (x > 0) and (x % col) == 0: r += ' '
			v = data[o2]
			if (v < 32) or (v > 127):
				c = '.'
			else:
				c = chr(v)
			r += c
			
			o2 += 1
			x += 1
		
		o = o2
		y += 1
	r += '\n'
	
	return r


class VTechGLCXBusIO:
	"Driver for the Arduino running VTechGLCXBusIO board intercepting bus traffic"
	
	def __init__(self):
		
		# The serial port to use
		self.ser = None
		
		# Store how often a combination of addr and data has been accessed
		self.on_bus = lambda addr, value, flags: True	# Dummy
		self.on_shutdown = lambda c: True	# Dummy
		
		self.running = False
		
		self.traffic_bytes = 0
		self.traffic_steps = 0
		self.traffic_chk_wrong = 0
		
		# for Binary protocol
		self.buf = bytearray(BUFFER_SIZE)
		self.buf_ofs_push = 0
		self.buf_ofs_pull = 0
		self.buf_waiting = 0
		
	
	def start(self):
		# Check your COM port and baud rate
		self.ser = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD, bytesize=serial.EIGHTBITS, stopbits=1, parity=serial.PARITY_NONE, xonxoff=False, rtscts=False, dsrdtr=False, timeout=0)
		put('Port is open!')
		
		
		# Reset statistics
		self.running = True
		self.traffic_bytes = 0
		self.traffic_steps = 0
		
		# for Binary protocol
		self.buf_ofs_push = 0
		self.buf_ofs_pull = 0
		self.buf_waiting = 0
		
		# for HEX protocol
		self.line_old = ''
		self.bus_flags_old = -1
		
		# Receive welcome message
		time.sleep(1.0)	# Wait for boot-up
		
		#for i in range(20):
		#	time.sleep(0.02)
		#	l = self.ser.readline()	#.strip()
		#	put('Header:	%s' % str(l))
		
		#for i in range(5):
		#	self.update(force_receive=True)
		#	time.sleep(0.1)	# Wait for boot-up
		
		time.sleep(COMMAND_LATENCY)	# Important! Must wait for buffer to be filled
		for i in range(3):
			time.sleep(0.1)
			data = self.ser.readline()
		
	
	def handle_line(self, l):
		# Parse simple HEX line "xxxxxx=xx"
		if len(l) != (6+1+2):
			put('Unhandled: "%s"' % str(l))
			return
		a = int(l[0:6], 16)
		d = int(l[7:9], 16)
		self.handle_bus(a, d, None)
	
	def handle_bus(self, bus_addr, bus_data, bus_flags):
		#put('%s = %06X	%s = %02X' % (to_bin(bus_addr, 16), bus_addr, to_bin(bus_data, 8), bus_data))
		
		
		"""
		bus_addr_lo = bus_addr & 0x7fff	# We bind the upper most bit to "something", so we should ignore it!
		if bus_addr_lo in WATCH_LIST:
			i = WATCH_LIST.index(bus_addr_lo)
			#if (i >= 0):
			ind = '.\t'
			put((ind * i) + ('%06X=%02X' % (bus_addr_lo, bus_data)) + (ind * (len(WATCH_LIST)-i-1)))
		
		if bus_addr in IGNORE_LIST:
			return
		"""
		
		
		"""
		if (bus_addr_lo == 0x0186) and (bus_data == 0x18):	# Happens on shutdown
			# This seems to come close to shutdown
			put('Shutdown signal!')
			self.on_shutdown(0)
			self.running = False
		"""
		
		"""
		c = chr(bus_data)
		if (bus_data < 20) or (bus_data > 127):	c = 'x%02x' % (bus_data)
		# Disable output to be more vigilant
		put('%s = %06X	%s = %02X = %s' % (to_bin(bus_addr, 16), bus_addr, to_bin(bus_data, 8), bus_data, c))
		#put('%06X	%02X = %s' % (bus_addr, bus_data, c))
		"""
		
		"""
		if RECORD_COMBOS:
			# Store combo
			#key = (bus_addr, bus_data)	# Access to addr AND data
			key = bus_addr	# Just count the address accesses
			if key in combos:
				combos[key] += 1
			else:
				combos[key] = 1
		"""
		
		# Handle
		self.on_bus(bus_addr, bus_data, bus_flags)
		
		# Store statistics
		self.traffic_steps += 1
		self.bus_flags_old = bus_flags
		
	
	def send_command(self, cmd):
		put('>>> %s' % str(cmd))
		if self.ser is None:
			return
		
		self.ser.write(cmd)
		#self.ser.flush()
	
	def update(self, count=5, force_receive=False):
		for rep in range(count):
			l = self.ser.inWaiting()
			#put('Waiting: %d bytes...' % l)
			
			# Patch for DUE: Only poll big packets! Don't poll each one
			if (l < BUFFER_SIZE_MIN_FLUSH) and (not force_receive): continue
			
			#put('Waiting: %d bytes...' % (l))
			if (self.buf_waiting + l) >= BUFFER_SIZE:
				# Clip to max
				l = BUFFER_SIZE - self.buf_waiting
			
			if l <= 0: continue
			
			#put('Receiving %d bytes...' % (l))
			data_in = self.ser.read(l)
			self.traffic_bytes += l
			
			#put('Got data: %d bytes: %s' % (len(data_in), str(data_in)))
			#put('Got data: %s' % str(data_in))
			#put('Got %d bytes' % len(data_in))
			
			try:
				t = self.line_old + data_in.decode('ascii')
			except UnicodeDecodeError:
				put('Encoding error!')
				# Reset proto
				t = ''
			
			lines = t.split('\r\n')
			self.line_old = lines.pop()	# Keep residue for next time
			for line in lines:
				self.handle_line(line)
			
			
			"""
			### Binary protocol
			if self.buf_waiting > BUFFER_SIZE-4:
				put('Input buffer overflow!')
			else:
				# Fetch new data
				#data_in = self.ser.read(self.ser.in_waiting)
				l = self.ser.inWaiting()
				
				# Patch for DUE: Only poll big packets! Don't poll each one
				if l > BUFFER_SIZE_MIN_FLUSH:
					#put('Waiting: %d bytes...' % (l))
					if (self.buf_waiting + l) >= BUFFER_SIZE:
						# Clip to max
						l = BUFFER_SIZE - self.buf_waiting
					
					if l > 0:
						#put('Receiving %d bytes...' % (l))
						data_in = self.ser.read(l)
					
						for b in data_in:
							self.buf[self.buf_ofs_push] = ord(b)
							self.buf_ofs_push = (self.buf_ofs_push + 1) % BUFFER_SIZE
							self.buf_waiting += 1
						
						self.traffic_bytes += l
			
			if self.buf_waiting < PACKET_SIZE:
				# Nothing to do
				return
			
			#put('Buffer: ofs_push=%d	ofs_pull=%d	buf_waiting=%d' % (self.buf_ofs_push, self.buf_ofs_pull, self.buf_waiting))
			#put(str(self.buf))
			
			o = self.buf_ofs_pull
			while (self.buf_waiting >= 4):
				
				# Try parsing at current ofs
				#put('Trying at %d...' % (o))
				bus_addr_hi = self.buf[o]
				o = (o + 1) % BUFFER_SIZE
				bus_addr_lo = self.buf[o]
				o = (o + 1) % BUFFER_SIZE
				
				bus_data = self.buf[o]
				o = (o + 1) % BUFFER_SIZE
				
				bus_flags_hi = self.buf[o]
				o = (o + 1) % BUFFER_SIZE
				bus_flags_lo = self.buf[o]
				o = (o + 1) % BUFFER_SIZE
				
				bus_chk = self.buf[o]
				o = (o + 1) % BUFFER_SIZE
				
				
				calc_chk = bus_addr_hi ^ bus_addr_lo ^ bus_data	# ^ bus_flags
				
				if calc_chk == bus_chk:
					# Okay!
					# Update offsets
					#self.buf_ofs_pull = (self.buf_ofs_pull + 4) % BUFFER_SIZE
					self.buf_waiting -= PACKET_SIZE
					self.buf_ofs_pull = o
					bus_addr = bus_addr_hi * 0x0100 + bus_addr_lo
					bus_flags = bus_flags_hi * 0x0100 + bus_flags_lo
					self.handle_bus(bus_addr, bus_data, bus_flags)
				else:
					# Checksum mismatch!
					#put('Checksums mismatch at %d: %02X != %02X' % (o, calc_chk, bus_chk))
					
					# Shift by one and try again next time
					self.buf_waiting -= 1
					self.buf_ofs_pull = (self.buf_ofs_pull + 1) % BUFFER_SIZE
					o = self.buf_ofs_pull
					self.traffic_chk_wrong += 1
				
			
			
			"""
		# End of outer repeater loop
	
	def stop(self):
		
		if self.ser is None:
			return
		
		time.sleep(0.2)
		self.ser.flush()
		time.sleep(0.2)
		self.ser.close()
	
	### Functions
	def pinmode_high_z(self):
		self.send_command(b'z')	# High-Z
	
	def pinmode_acquire_r(self):
		self.send_command(b'a')	# Acquire bus for reading
	
	def pinmode_acquire_w(self):
		self.send_command(b'A')	# Acquire bus for writing, keeping nWE HIGH
	
	def set_ncs2_low(self):
		self.send_command(b'c')	# Set the nCS2 line LOW
	
	def set_ncs2_high(self):
		self.send_command(b'C')	# Set the nCS2 line HIGH
	
	def monitor_start(self):
		# Start monitoring
		#self.pinmode_acquire_r()
		self.pinmode_high_z()
		self.send_command(b'm')
	def monitor_stop(self):
		#self.send_command(b'M')
		self.send_command(b's')
		#self.pinmode_high_z()
	
	def dump(self, addr=0x00000000, l=0x100, beautify=True):
		#self.pinmode_acquire_r()
		
		self.send_command(b'd%08X%08X' % (addr, l))
		
		time.sleep(COMMAND_LATENCY)	# Important! Must wait for buffer to be filled
		
		for i in range(1+(l//16)+0):
			time.sleep(LINE_LATENCY)
			data = self.ser.readline()
			if (len(data) == 0):
				time.sleep(0.1)
				data = self.ser.readline()
			t = data.decode('ascii').strip()
			
			if beautify:
				# Beautify / Extract printable characters
				if ':' in t:
					hex = t[t.index(':')+1:].strip()
					t2 = t[:t.index(':')+1] + '\t'
					t = ''
					for i in range(len(hex)//2):
						v = int(hex[i*2:i*2+2], 16)
						t2 += '%02X ' % v
						if v < 0x20 or v >= 0x80:
							t += '.'
						else:
							t += chr(v)
					t = t2 + '\t' + t
			
			put(t)
		
	def write(self, addr, data):
		#self.pinmode_acquire_w()
		if type(data) is int:
			# Single value
			self.send_command(b'w%08X%02X' % (addr, data))
		
		elif type(data) is list:
			# List of values
			l = len(data)
			s = b''.join([ b'%02X'%v for v in data ])
			self.send_command(b'W%08X%08X%s' % (addr, l, s))
			#for v in data: self.send_command(b'%02X' % v)
		else:
			put('values must be single int or list of ints')
			return
		#time.sleep(COMMAND_LATENCY)	# Important! Must wait for buffer to be filled
		for i in range(1):
			time.sleep(LINE_LATENCY)
			data = self.ser.readline()
			#put(data)



class VTechVis:
	"The virtual representation of the VTech Genius Leader computer"
	
	def __init__(self, name='main', addr_offset=0, mem_size=BANK_SIZE, pos=(PADDING, PADDING), width=BANK_WIDTH):
		self.name = name
		self.addr_offset = addr_offset
		self.mem_size = mem_size
		
		#self.mem = bytearray(self.mem_size)
		self.addr_select = self.addr_offset	# currently selected address
		#self.video_mem = # Point to vtbi.mem[1CA0:1CF0]
		self.is_selected = False
		
		self.mem = bytearray(self.mem_size)
		self.usage = numpy.zeros(self.mem_size, dtype=int)
		
		# Gfx stuff
		self.pos = pos
		self.width = width	#256
		self.height = int(math.ceil(self.mem_size / self.width))
		self.size = (self.width, self.height)
		
		surfaceDepth = 32
		self.surface = pygame.Surface(self.size, depth=surfaceDepth)
		self.surfaceZoom2 = pygame.Surface((self.size[0] * 2, self.size[1] * 2), depth=surfaceDepth)
		self.surfaceZoom3 = pygame.Surface((self.size[0] * 3, self.size[1] * 3), depth=surfaceDepth)
		self.surfaceZoom4 = pygame.Surface((self.size[0] * 4, self.size[1] * 4), depth=surfaceDepth)
		#self.surface_array = pygame.surfarray.pixels2d(self.surface)	# Create a surface-REFERENCED array!
		#self.surface_array = pygame.PixelArray(self.surface)	# Create a surface-REFERENCED array!
		#self.surface = pygame.surfarray.make_surface(self.mem)
		#pygame.pixelcopy.surface_to_array(self.surface, self.mem_array, kind='P')
		#self.surface.lock()
		
		self.fade = True
		self.surface_black = pygame.Surface(self.size)
		#self.surface_black.fill((255,255,255))
		self.surface_black.fill((1, 32, 0))
	
	def clear_mem(self):
		for i in range(len(self.mem)):
			self.mem[i] = 0
		for i in range(len(self.usage)):
			self.usage[i] = 0
	
	def pos_to_addr(self, p):
		x = max(0, min(self.width-1, (p[0] - self.pos[0]) // ZOOM))
		y = max(0, min(self.height-1, (p[1] - self.pos[1]) // ZOOM))
		return self.addr_offset + (x + y*self.width)
	
	def addr_to_pos(self, addr):
		# Wrap around
		#a = addr % MEMORY_SIZE
		
		# Filter
		a = addr - self.addr_offset
		if a < 0: a = 0
		if a >= self.mem_size: a = self.mem_size-1
		
		x = a % self.width
		y = a //self.width
		return(self.pos[0] + x * ZOOM + ZOOM//2, self.pos[1] + y * ZOOM + ZOOM//2)
	
	def handle_bus(self, addr, data, flags):
		# Store in memory map
		
		# Wrap around
		#a = addr % MEMORY_SIZE
		
		# Filter
		a = addr - self.addr_offset
		if a < 0: return
		if a >= self.mem_size: return
		
		
		self.mem[a] = data
		self.usage[a] += 1
		
		#@FIXME: set_at() is really uncool to use! I want hardware pixel surface arrays!!
		#self.surface_array[] = value
		#col = (0xff, 0xff, value)
		self.surface.set_at((a % self.width, a // self.width), (0xff, 0xff, 0x7f + data//2) )
		
	
	def clear_surface(self):
		self.surface.fill((0,0,0))
	
	def draw(self, screen):
		
		if ZOOM == 4:
			pygame.transform.scale2x(self.surface, self.surfaceZoom2)
			pygame.transform.scale2x(self.surfaceZoom2, self.surfaceZoom4)
			screen.blit(self.surfaceZoom4, self.pos)
		elif ZOOM == 3:
			pygame.transform.scale(self.surface, (self.size[0]*3, self.size[1]*3), self.surfaceZoom3)
			screen.blit(self.surfaceZoom3, self.pos)
		elif ZOOM == 2:
			screen.blit(pygame.transform.scale2x(self.surface), self.pos)
		else:
			screen.blit(self.surface, self.pos)
		
		if self.fade:
			# Darken the surface / Fade out
			self.surface.blit(self.surface_black, (0,0), special_flags=BLEND_SUB)
		else:
			# Clear
			self.surface.fill((0,0,0))
		
		if self.is_selected:
			# Highlight selected address
			col = (0x00, 0xff, 0x80)
			a = self.addr_select - self.addr_offset
			#p = self.addr_to_pos(self.addr_select)
			#pygame.draw.circle(screen, col, p, ZOOM*2, 1)
			#pygame.draw.rect(screen, col, [p[0]-ZOOM, p[1]-ZOOM, ZOOM*3, ZOOM*3], False)
			x = self.pos[0] + (a % self.width)*ZOOM
			y = self.pos[1] + (a //self.width)*ZOOM
			pygame.draw.rect(screen, col, [x-ZOOM, y-ZOOM, ZOOM*3 -1, ZOOM*3-1], ZOOM)
		
	def save_mem(self, filename):
		put('Writing dump to "%s"...' % (filename))
		with open(filename, 'wb+') as h:
			h.write(self.mem)
	
	def save_combos(self, filename, sort_by_count=False):
		put('Writing combos...')
		if sort_by_count:
			from operator import itemgetter
			with open(filename + '.access.byCount', 'wb+') as h:
				for kv in sorted(self.combos.items(), key=itemgetter(1), reverse=True):
					#combo = self.combos[k]
					k, v = kv
					s = 'A %06X	C %d\n' % (k, v)
					h.write(s)
				#
		else:
			with open(filename + '.access.byAddr', 'wb+') as h:
				for k in sorted(self.combos):
					v = self.combos[k]
					#s = 'A %06X	D %02X	C %d\n' % (k[0], k[1], v)
					s = 'A %06X	C %d\n' % (k, v)
					h.write(s)
		# End of combo writing
	




def run_vis():
	# Init game
	put('Initializing screen...')
	pygame.init()
	screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
	clock = pygame.time.Clock()
	font = pygame.font.SysFont('Lucida Console', 14, False)	#True)
	pygame.display.set_caption(VERSION)
	#pygame.mouse.set_visible(False)
	screen.fill((0x33, 0xcc, 0x99))
	
	def draw_text(screen, text, p):
		img = font.render(text, True, (255,255,255))
		rect = img.get_rect()
		rect[0] = p[0]
		rect[1] = p[1]
		screen.blit(img, rect)
		return img
	
	vtvs = [
		VTechVis(name='M0', addr_offset=0x000000, mem_size=BANK_SIZE),
		VTechVis(name='M1', addr_offset=BANK_SIZE, mem_size=BANK_SIZE)
	]
	vtv = vtvs[0]
	burst_dump = False
	
	i = 0
	x = PADDING
	y = PADDING
	for v in vtvs:
		#put('x=%d, y=%d' % (x, y))
		if (x+v.width*ZOOM > SCREEN_SIZE[0]-PADDING):
			#put('x=%d+%d > %d' % (x, v.width*ZOOM, SCREEN_SIZE[0]-PADDING))
			x = PADDING
			y += v.height*ZOOM + PADDING
		
		#v.pos = ( PADDING + (i%BANKS_X)*(BANK_WIDTH*ZOOM+PADDING),	PADDING + (i//BANKS_X)*(BANK_HEIGHT*ZOOM+PADDING))
		v.pos = (x, y)
		v.draw(screen)
		v.is_selected = (v == vtv)
		x += v.width*ZOOM
		
		i += 1
	
	put('Starting interceptor...')
	vtbi = VTechGLCXBusIO()
	
	def vtbi_onbus(addr, data, flags):
		if (burst_dump) or (addr in WATCH_LIST):
			put('Addr: %06X = %02X' % (addr, data))
		
		for v in vtvs:
			v.handle_bus(addr, data, None)
		
	#vtbi.on_bus = vtv.handle_bus
	vtbi.on_bus = vtbi_onbus
	vtbi.start()
	
	if DUMMY_ACTIVITY:
		pass
	else:
		vtbi.monitor_start()
	
	key_retrig = 0
	traffic_display = False
	traffic_time_last = time.time()
	
	running = True
	put('Running...')
	
	frame = 0
	while running:
		tick = clock.tick(50)
		
		# Do the work
		
		if DUMMY_ACTIVITY:
			# Test
			addr = random.randint(0, MEMORY_SIZE * 2)
			data = random.randint(0, 255)
			vtbi_onbus(addr, data, None)
		else:
			#vtbi.update(count=100 if vtbi.running else 1)
			vtbi.update(2)	# Due wants to send bulk, so do not poll it to often
		
		
		# Maybe update from time to time?
		if True:
			step = 8 if (pygame.key.get_mods() & (KMOD_SHIFT | KMOD_LSHIFT)) else 1
			
			for event in pygame.event.get():
				if event.type == QUIT:
					exit()
				
				if event.type == MOUSEBUTTONDOWN:
					# Update all
					for v in vtvs:
						v.is_selected = False
						if event.pos[0] < v.pos[0]: continue
						if event.pos[0] >= v.pos[0]+v.size[0]: continue
						if event.pos[1] < v.pos[1]: continue
						if event.pos[1] >= v.pos[1]+v.size[1]: continue
						vtv = v
						v.is_selected = True
						
						addr = v.pos_to_addr(event.pos)
						data = v.mem[addr - v.addr_offset]
						put('Addr: %06X = %02X' % (addr, data))
						v.addr_select = addr
						put(to_hexdump(v.mem, v.addr_select - v.addr_offset, 0x100, v.addr_offset))
						
				"""
				if event.type == MOUSEMOTION:
					#trace("x=" + str(event.pos[0]) + ", y=" + str(event.pos[1]), 0, False)
					#addr = vtv.pos_to_addr(event.pos)
					#put('Addr: %06X	=	%02X' % (addr, vtbi.mem[addr]))
					#vtv.addr_select = addr
					pass
				"""
				
				if event.type == KEYDOWN:
					key_retrig = KEY_RETRIG_DELAY
					
					if (event.key == K_ESCAPE):
						running = False
					elif (event.key == K_BACKSPACE):
						vtv.clear_surface()
						vtv.clear_mem()
						
					elif (event.key == K_TAB):
						i = vtvs.index(vtv)
						i = (i + 1) % len(vtvs)
						vtv = vtvs[i]
						for v in vtvs: v.is_selected = (v == vtv)
					
					elif (event.key == K_SPACE):
						
						burst_dump = True
						
						# Stop
						#vtbi.send_command(b's')
						"""
						vtv.set_masks(maskC=TRIGGER_MASK_C, valC=TRIGGER_VAL_C, maskD=TRIGGER_MASK_D, valD=TRIGGER_VAL_D)
						vtv.start_streaming(pin=TRIGGER_PIN, edge=TRIGGER_EDGE)
						
					elif (event.key == K_F1):
						addr_hi_mask = 0b0000000001
					elif (event.key == K_F2):
						addr_hi_mask = 0b0000000010
						"""
					
					elif (event.key == ord('m')):
						# Start monitoring
						vtbi.send_command(b'm')
					
					elif (event.key == ord('t')):
						traffic_display = not traffic_display
						put('traffic_display: ' + str(traffic_display))
					
					elif (event.key == ord('d')):
						# Dump region
						put(to_hexdump(vtv.mem, vtv.addr_select, 0x100, vtv.addr_offset))
					
					elif (event.key == ord('s')):
						timeStamp = time.strftime('%Y-%m-%d_%H-%M-%S')
						filename ='dumps/VT_' + timeStamp + '.' + vtv.name + '.mem'
						
						put('Saving to "' + filename + '"...')
						vtv.save_mem(filename)
						
					
					elif (event.key == ord('f')):
						#put('Last known BUS flags: %s' % (to_bin(vtbi.bus_flags_old, 16)))
						vtv.fade = not vtv.fade
						
					elif (event.key == ord('i')):
						
						c = 'i%02X%01X' % (ROM_PINNAME_TO_ARDUINO_PIN['RD'], EDGE_RISING)
						put('Inject... "' + c + '"...')
						vtbi.send_command(c)
						
						"""
					elif (event.key == ord('i')):
						put('IGNORE_LIST add 0x%06X' % (vtv.addr_select))
						if vtv.addr_select in IGNORE_LIST:
							pass	#IGNORE_LIST.remove(vtv.addr_select)
						else:
							IGNORE_LIST.append(vtv.addr_select)
						"""
					elif (event.key == ord('u')):
						put('IGNORE_LIST remove 0x%06X' % (vtv.addr_select))
						if vtv.addr_select in IGNORE_LIST:
							IGNORE_LIST.remove(vtv.addr_select)
						else:
							pass	#IGNORE_LIST.append(vtv.addr_select)
						
					elif (event.key == ord('w')):
						put('WATCH_LIST add 0x%06X' % (vtv.addr_select))
						if vtv.addr_select in WATCH_LIST:
							pass
						else:
							WATCH_LIST.append(vtv.addr_select)
					elif (event.key == ord('q')):
						put('WATCH_LIST remove 0x%06X' % (vtv.addr_select))
						if vtv.addr_select in WATCH_LIST:
							WATCH_LIST.remove(vtv.addr_select)
						else:
							pass
						
					
					elif (event.key == K_UP):
						vtv.addr_select = max(vtv.addr_offset + (vtv.addr_select-vtv.addr_offset) % vtv.width, vtv.addr_select - vtv.width*step)
					elif (event.key == K_DOWN):
						vtv.addr_select = min(vtv.addr_offset + vtv.mem_size-1, vtv.addr_select + vtv.width*step)
					elif (event.key == K_LEFT):
						vtv.addr_select = max(vtv.addr_offset, vtv.addr_select - step)
					elif (event.key == K_RIGHT):
						vtv.addr_select = min(vtv.addr_offset + vtv.mem_size-1, vtv.addr_select + step)
					elif (event.key == K_PAGEUP):
						vtv.addr_select = max(vtv.addr_select % vtv.width, PAGE_STEP * (vtv.addr_select // PAGE_STEP - step))
					elif (event.key == K_PAGEDOWN):
						vtv.addr_select = min(vtv.addr_offset + vtv.mem_size-1, PAGE_STEP * (vtv.addr_select // PAGE_STEP + step))
					elif (event.key == K_HOME):
						if event.mod & (KMOD_CTRL | KMOD_LCTRL):
							vtv.addr_select = vtv.addr_offset
						else:
							vtv.addr_select = vtv.pos_to_addr([vtv.pos[0], vtv.addr_to_pos(vtv.addr_select)[1]])
					elif (event.key == K_END):
						if event.mod & (KMOD_CTRL | KMOD_LCTRL):
							vtv.addr_select = vtv.addr_offset + vtv.mem_size-1
						else:
							vtv.addr_select = vtv.pos_to_addr([vtv.pos[0]+vtv.size[0], vtv.addr_to_pos(vtv.addr_select)[1]])
					
					else:
						put('unhandled: key=' + str(event.key))
					
				if event.type == KEYUP:
					if (event.key == K_SPACE):
						burst_dump = False
					
			# end of event loop
			
			if (key_retrig <= 0):
				pressed = pygame.key.get_pressed()
				if pressed[K_UP]:
					vtv.addr_select = max(vtv.addr_select % vtv.width, vtv.addr_select - vtv.width*step)
				if pressed[K_DOWN]:
					vtv.addr_select = min(vtv.addr_offset + vtv.mem_size-1, vtv.addr_select + vtv.width*step)
				if pressed[K_LEFT]:
					vtv.addr_select = max(vtv.addr_offset, vtv.addr_select - step)
				if pressed[K_RIGHT]:
					vtv.addr_select = min(vtv.addr_offset + vtv.mem_size-1, vtv.addr_select + step)
				if pressed[K_PAGEUP]:
					vtv.addr_select = max(vtv.addr_offset + (vtv.addr_select-vtv.addr_offset) % vtv.width, PAGE_STEP * (vtv.addr_select // PAGE_STEP - step))
				if pressed[K_PAGEDOWN]:
					vtv.addr_select = min(vtv.mem_size-1, PAGE_STEP * (vtv.addr_select // PAGE_STEP + step))
				key_retrig = KEY_RETRIG_DELAY2
			else:
				key_retrig -= 1
			
			#screen.fill((0x33, 0xcc, 0x99))
			screen.fill((0x33, 0xcc, 0x99), (0,0, SCREEN_SIZE[0], 16))
			draw_text(screen, 'Addr: %06X = %02X' % (vtv.addr_select, vtv.mem[vtv.addr_select - vtv.addr_offset]), (0, 0))
			
			for v in vtvs:
				v.draw(screen)
			
			pygame.display.update()
			
			if traffic_display:
				t = time.time()
				d = t - traffic_time_last
				if d > 1.0:
					put('Traffic: %d Bytes/s	%d steps/s	%d Checksums mismatch' % (vtbi.traffic_bytes / d, vtbi.traffic_steps, vtbi.traffic_chk_wrong))
					vtbi.traffic_bytes = 0
					vtbi.traffic_steps = 0
					vtbi.traffic_chk_wrong = 0
					traffic_time_last = t
			
		
		frame += 1
	
	"""
	put('Usage:')
	usage_ranking = numpy.argsort(vtbi.usage)
	for addr in reversed(usage_ranking):
		u = vtbi.usage[addr]
		if (u == 0): break
		put('	%06X	x %d' % (addr, u))
	"""
	
	"""
	put('WATCH_LIST: ' + str(WATCH_LIST))
	put('IGNORE_LIST: ' + str(IGNORE_LIST))
	"""
	
	put('Stopping...')
	vtbi.monitor_stop()
	vtbi.stop()
	put('Finished.')

def run_dump(ofs=0, size=0x200, beautify=True):
	vtbi = VTechGLCXBusIO()
	vtbi.start()
	
	# Change the first filename
	#vtbi.dump(0x00001b80, 0x20)
	#vtbi.write(0x00001b8c, [ ord(c) for c in 'PYTHON42' ])
	#vtbi.dump(0x00001b80, 0x20)
	vtbi.pinmode_acquire_r()
	vtbi.set_ncs2_low()
	
	#vtbi.dump(0x00000000, 0x200)
	#vtbi.dump(0x00000000, 0x1000)
	#vtbi.dump(0x00000000, 0x20000)	# Englisch fuer Anfaenger
	vtbi.dump(ofs, size, beautify=beautify)
	
	vtbi.set_ncs2_high()
	vtbi.pinmode_high_z()
	vtbi.stop()

def run_write():
	# Write contents
	#filename_bin = '/z/data/_devices/VTech_Genius_Lerncomputer/Cartridges/GLCX_Englisch_fuer_Anfaenger/CART_GLCX_Englisch_fuer_Anfaenger.dump.000-efa.bin'
	#filename_bin = '/z/data/_devices/VTech_Genius_Lerncomputer/Cartridges/GLCX_Englisch_fuer_Anfaenger/CART_GLCX_Englisch_fuer_Anfaenger.dump.000-lmu.bin'
	#filename_bin = '/z/data/_devices/VTech_Genius_Lerncomputer/Cartridges/GLCX_Update_Programm-Zusatzkassette/CART_GLCX_Update_Programm-Zusatzkassette.dump.000-oneShort.bin'
	filename_bin = '/z/data/_devices/VTech_Genius_Lerncomputer/Cartridges/GLCX_Englisch_fuer_Anfaenger/CART_GLCX_Englisch_fuer_Anfaenger.EFA.dedupe.bin'
	with open(filename_bin, 'rb') as h:
		data = h.read()
	
	l = len(data)
	put('Data size: %d bytes = 0x%08X' % (l, l))
	
	vtbi = VTechGLCXBusIO()
	vtbi.start()
	
	chunk_size = 32
	addr = 0x00000000
	
	# Limit max size
	#l = 0x200
	
	vtbi.pinmode_acquire_w()
	vtbi.set_ncs2_low()
	
	time.sleep(0.1)
	
	o = 0
	while(o < l):
		d2 = data[o:o+chunk_size]
		l2 = len(d2)
		put('Chunk: addr=0x%08X len=%d' % (addr, l2))
		vtbi.write(addr, [ c for c in d2 ])
		
		addr += l2
		o += l2
	put('%d bytes written.' % o)
	
	
	#@FIXME: I have no idea why the first page gets overwritten with junk (always the identical junk)
	# Does it happen during writing or afterwards?
	# Might be due to my crappy wiring on the physical side...
	
	# Re-write first chunk
	for i in range(2):
		time.sleep(0.2)
		l = 128
		addr = 0
		o = 0
		while(o < l):
			d2 = data[o:o+chunk_size]
			l2 = len(d2)
			put('Chunk: addr=0x%08X len=%d' % (addr, l2))
			vtbi.write(addr, [ c for c in d2 ])
			
			addr += l2
			o += l2
		put('%d bytes written.' % o)
	
	
	# Make the adress pins point to an "unimportant"/unused address...
	vtbi.write(0xfffffff0, 0xff)
	
	# ...so we can manually set the WRITE line without corrupting any useful bytes
	put('Set write protect now!')
	
	#vtbi.pinmode_acquire_w()
	time.sleep(6)
	
	# Read back and see if we corrupted anything
	vtbi.pinmode_acquire_r()
	vtbi.set_ncs2_low()
	
	vtbi.dump(0x00000000, 0x200)
	
	vtbi.set_ncs2_high()
	vtbi.pinmode_high_z()
	
	vtbi.stop()
	

if __name__ == '__main__':
	#run_vis()
	
	#run_dump()
	#run_dump(ofs=0x80000 - 0x2000, size=0x4000)
	#run_dump(ofs=0x00000, size=0x200000, beautify=False)	# 2M = 2097152 = 0x200000
	
	run_write()
	run_dump()
