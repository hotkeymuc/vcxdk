filename_in = 'GLCX_MagiCam__VTechGLCXBusIO-dumped-first-64K.001.hex'
filename_out = filename_in + '.bin'

r = []

# Read hex text input
for l in open(filename_in, 'r'):
	l = l.strip()
	if ':' in l:
		l = l[l.index(':')+1:].strip()
	for i in range(len(l)//2):
		v = int(l[i*2:i*2+2], 16)
		r.append(v)

# Write binary output
with open(filename_out, 'wb') as h:
	h.write(bytes(r))