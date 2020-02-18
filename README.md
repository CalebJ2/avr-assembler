# avr-assembler

Assembles a subset of Atmel's AVR assembly. https://www.microchip.com/webdoc/avrassembler/index.html

Written to learn about the AVR architecture and assembler process. Not written as an example of good parser design or coding practices. But hopefully it is fairly well commented.

See the wiki for more resources: https://github.com/CalebJ2/avr-assembler/wiki

Run with `python main.py <filename>`. Written for python 2.7 because that's what I happened to have installed.

Supported preprocessor features:
- `.include`
- `.equ`
- `;`, `//`, `/* */`
- labels
- binary (0b), hex (0x) and decimal (no prefix) numbers

Limitations:
- Incomplete instruction set. See instructions.json for supported instructions.
- Things like preprocessor operators and macros not supported
- Most assembler directives unsupported
- rjmp instruction target must be a label or absolute address
- Program size must be less than 256 bytes
- Probably buggy