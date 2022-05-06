# VCXDK
Unofficial software development kit (SDK) for the VTech "CX" line of learning computers

Goal is to have a simple way to compile homebrew ROM cartridges that can be run on any VTech computer of that model line.

These machines are based on a proprietary CompactRISC CPU, the National Semiconductor **CR16B**. The rest of the hardware is widely unknown, which makes things quite "spicy".
Fortunately, there are two starting points:

* National Semiconductor's *CR16B Developer Toolkit* is [available from the Wayback Machine.](https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/files/CR16C31.exe)

* MAME contains a disassembler for that CPU (but no actual emulation, yet)


## Target platforms
* VTech Genius LEADER 5005 X [de]
* VTech BrainStation 5505 X [de]
* VTech Genius LEADER 6600 CX [de]*
* VTech Genius LEADER 8008 CX [de]
* VTech Genius MASTER e-Power X [de]
* EDITRICE GIOCHI Computer Bit Communicator parlante [it]
* VTech BrainStation 9009 CXL [de]
* VTech Genius TableTop Black Magic CX [de]
* (more)*

(Marked models are untested, i.e. I don't have a physical one to test... yet)


## History
* 2022-05-05 Successfully compiled and assembled a very basic C file, which then ran on real hardware!
* 2022-05-01 We got code execution on a custom compiled ROM using the simple cr16b_asm assembler!
* 2022-04-10 Got small EEPROMS, started on a bespoke simple assembler
* 2022-03-25 Working on a development cartridge, but those 3.3V EEPROMs are quite finicky compared to those old 5V ones used with the Z80 models. Meanwhile, a "Computer Bit Communicator" arrived from bella Italia! Looks like a "Genius MASTER e-Power X", but comes with the RS232 level converter cable and "E-Mail" cartridge included. Nice. Also, totally love the italian speech. Ciao!
* 2022-03-15 Took a high-res image of the 8008 CX screen, counted the pixels (240 x 144) and found those two values being used as a pair in some early regions of the firmware - Houston, we got some graphics entry points!
* 2022-03-13 Trying to use a "SuperSpeicher (CX)" RAM cartridge as a program cartridge. No luck so far. There seem to be some more cartridge type checks I am missing.
* 2022-03-08 Got a basic understanding of the 8008 CX firmware structure. Currently waiting for 3.3V parallel EEPROMs to arrive, so I can have a try at code execution.
* 2022-03-10 Analyzing the different cartridges: There are ROM ones, there are RAM ones ("SuperSpeicher"); the "E-Mail" cartridge even has 1x ROM and 2x battery-backed RAM on a single PCB.
* 2022-03-04 Hooked up an Arduino DUE to the 8008 CX cartridge bus, dumping all the ROMs I can find.
* 2022-03-03 Created my own disassembler in Python using the MAME disassembler as a template.
* 2022-01-30 Looked further into the "Genius LEADER 8008 CX" and noticed that there is no proper emulation for it. In fact, almost nothing is known about the hardware. On Team Europe's blog I read that the processor is a CR16B by National Semiconductor - a custom, quite "exotic" CPU... I am intrigued!
* 2016 - 2021 Work on VGLDK for Z80 based systems, quite usable so far.

## Further Reading
* [Team Europe's Dumping Blog on VTech](https://team-europe.blogspot.com/2017/03/decapping-is-fun-world-3.html)
* National Semiconductor's CR16B toolset (installer executable is still available on the Wayback machine):
  * [Download Overview](https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/0,3303,838,00.html)
  * [Installer .EXE](https://web.archive.org/web/20040530110107/http://www.national.com/appinfo/compactrisc/files/CR16C31.exe) (unpack the file using "unshield" under Linux; run the tools using Wine)
* [MAME's CR16B implementation](https://github.com/mamedev/mame/tree/master/src/devices/cpu/cr16b)
* [Ghidra's CR16B stub](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/CR16/data/languages/CR16B.sinc)
* [VGLDK for older Z80 based VTech computers](https://github.com/hotkeymuc/vgldk)

2022-03-08 Bernhard "HotKey" Slawik