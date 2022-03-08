# VCXDK
Unofficial software development kit (SDK) for the VTech's "CX" line of learning computers

These machines are based on a proprietary CompactRISC CPU, the National Semiconductor CR16B. The rest of the hardware is widely unknown, which makes things quite "spicy".
Fortunately, there are two starting points:
* National Semiconductor's CR16B developer toolkit is still stored in the wayback machine!
* MAME contains a disassembler for that CPU (but no actual emulation as of writing this message)

Goal is to have a simple way to compile ROM cartridges that can be run on any VTech computer of that model line.

## Target platforms
* Genius LEADER 5005 X
* Genius LEADER 6600 CX (untested)
* Genius LEADER 8008 CX
* Genius TableTop Black Magic 8008 CX
* Genius BrainStation 5505 X (untested)
* BrainStation 9009 CXL
* Genius MASTER e-Power X
* Computer Bit Communicator (untested)
* (probably much more)

## History
* 2021-03-08 Got a basic understanding of the 8008 CX firmware. Currently waiting for 3.3V parallel EEPROMs to arrive.
* 2021-03-04 Hooked up an Arduino DUE to the 8008 CX cartridge port, dumping all the ROMs I can find.
* 2021-03-03 Created my own disassembler in Python using the MAME disassembler as a template.
* 2021-01-30 Looked further into the "Genius LEADER 8008 CX" and noticed that there is no prober emulation for it. In fact, almost nothing is known about the hardware. On Team Europe's blog I read that the processor is a CR16B by National Semiconductor - a custom, quite "exotic" CPU... I am intrigued!
* 2016 - 2021 Work on VGLDK for Z80 based systems, quite usable so far.

## Further Reading
* [Team Europe Dumping Blog on VTech](https://team-europe.blogspot.com/2017/03/decapping-is-fun-world-3.html)
* National Semiconductor's CR16B toolset (installer executable is still available on the Wayback machine):
  * [Download Overview](https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/0,3303,838,00.html)
  * [Installer .EXE](https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/files/CR16C31.exe) (unpack the file using "unshield" under Linux; run the tools using Wine)
* [MAME's CR16B implementation](https://github.com/mamedev/mame/tree/master/src/devices/cpu/cr16b)
* [Ghidra's CR16B stub](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/CR16/data/languages/CR16B.sinc)
* [VGLDK for Z80 based VTech computers](https://github.com/hotkeymuc/vgldk)

2022-03-08 Bernhard "HotKey" Slawik