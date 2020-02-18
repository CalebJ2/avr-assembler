# avr-assembler

Assembles a subset of Atmel's AVR assembly. https://www.microchip.com/webdoc/avrassembler/index.html

Run with `python main.py <filename>`. Written for python 2.7 because that's what I happened to have installed.

Supported preprocessor features:
- `.include`
- `.equ`
- `;`, `//`, `/* */`
- labels
- binary (0b), hex (0x) and decimal (no prefix) numbers

Things like preprocessor operators and macros not supported.

See instructions.json for supported instructions.