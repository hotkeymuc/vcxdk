# VCXDK
A development kit (SDK) for the CR16B based VTech "CX" line of learning computers

These machines are widely undocumented, which makes things difficult.
I found National Semiconductor's CR16B developer tools inside the wayback machine!
MAME contains a disassembler for that CPU (but no actual emulation as of writing this message).

## Target platforms
* Genius LEADER 5005 X
* Genius LEADER 6600 CX
* Genius LEADER 8008 CX
* Black Magic 8008 CX
* Genius BrainStation 5505 X
* BrainStation 9009 CXL
* ...

## History
* 2021-03-08 Got a basic understanding of the 8008 CX firmware. Currently waiting for 3.3V parallel EEPROMs to arrive.
* 2021-03-04 Hooked up an Arduino DUE to the 8008 CX cartridge port, dumping all the ROMs I can find.
* 2021-03-03 Created my own disassembler in Python using the MAME disassembler as a template.
* 2021-01-30 Looked further into the "Genius LEADER 8008 CX" and noticed that there is no prober emulation for it. In fact, almost nothing is known about the hardware. On Team Europe's blog I read that the processor is a CR16B by National Semiconductor - a custom, quite "exotic" CPU... I am intrigued!
* 2016 - 2021 Work on VGLDK for Z80 based systems, quite usable so far.

## Further Reading
* "Team Europe" on VTech: https://team-europe.blogspot.com/2017/03/decapping-is-fun-world-3.html
* National Semiconductor's CR16B toolset (installer executable is still available on the Wayback machine):
  * Download page: https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/0,3303,838,00.html
  * The installer file itself (unpack the file using "unshield" under Linux; run the tools using Wine): https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/files/CR16C31.exe
* MAME's CR16B (disassembler): https://github.com/mamedev/mame/tree/master/src/devices/cpu/cr16b
* Ghidra's CR16B stub: https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/CR16/data/languages/CR16B.sinc
* Old VGLDK on Github for Z80 based VTech computers: https://github.com/hotkeymuc/vgldk

2022-03-08 Bernhard "HotKey" Slawik