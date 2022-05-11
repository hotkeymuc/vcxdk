; This file can be pre-pended to generate a working VTech Genius CX cartridge

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
;ofs 0x180
;.str_hello:
;	db      'Hello world!',0x00
;.str_htk:
;	db      'HotKey was here!',0x00

; Define some symbols we need for a successful compile
.rdata_2:

;_printf:
;	push $2, era
;	popret $2, era


; TEXT: Actual code (at offset 0x200)
ofs 0x200	; Hard-coded entry point when invoking the cartridge
	br _main


; Some trials agains VTech Genius Leader 8008 CX [de]
;	; Show a prompt (Y/N)
;	movd    $0x034191, (r1,r0)	; Dunno what this param does...
;	push    $2, r0
;	
;	movd    .str_hello, (r3,r2)	; Use our own constant
;	adduw   $0x10, r3	; Add the cartridge ROM base address (0x100000)
;	movd    .str_htk, (r5,r4)	; Use our own constant
;	adduw   $0x10, r5	; Add the cartridge ROM base address (0x100000)
;	
;	bal     (ra,era), 0x1805C4	; prompt_yesno__title_r3r2__text_r5r4__sys5c4 (0x0005C4 + internal ROM offset 0x180000)
;	adduw   $0x4, sp
;	
;	; Check the result in r0
;	cmpb    $0x1, r0	; 1 = YES, 0 = NO
;	beq     .start	; Back to start
;	;beq     .end	; Exit out


;	; Show an alert
;	movd    $0x035171, (r1,r0)	; Dunno what this param does
;	adduw   $-0x8, sp
;	storw   r0, 0x4(sp)
;	storw   r1, 0x6(sp)
;	movw    sp, r0
;	adduw   $0x32, r0
;	movw    $0, r1
;	storw   r0, 0(sp)
;	storw   r1, 0x2(sp)
;	movb    $0x01, r4
;	
;	;movd    $0x0898D7, (r3,r2)	; 0x0898D7 = STRING "Alarm"
;	movd    .str_htk, (r3,r2)	; Use our own constant
;	adduw   $0x10, r3	; Add the cartridge ROM base address (0x100000)
;	
;	bal     (ra,era), 0x198D18	; 0x018D18 + 0x180000
;	adduw   $0x8, sp
;	bal     (ra,era), 0x180424	; 0x000424 + 0x180000



;	; Show a popup
;	movd    $0x034191, (r1,r0)	; Dunno what this param does
;	adduw   $-0x8, sp
;	storw   r0, 0x4(sp)
;	storw   r1, 0x6(sp)
;	
;	movd    .str_htk, (r1,r0)	; Use our own constant
;	adduw   $0x10, r1	; Add the cartridge ROM base address (0x100000)
;	
;	storw   r0, 0(sp)
;	storw   r1, 0x2(sp)
;	
;	movb    $0, r4
;	movd    $0x084D40, (r3,r2)	; Dunno what this param does
;	bal     (ra,era), 0x198CC4	; show_info_popup_r1r0 (0x018CC4 + internal ROM offset 0x180000)
;	adduw   $0x8, sp


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

