;hello.asm
;  turns on an LED which is connected to PB5 (digital out 13)

.include "./m328Pdef.inc"

    ldi r16,0b00100000
    out DDRB,r16   ; Set data direction to out
    out PortB,r16  ; Set pins high or low
Start:
    rjmp Start