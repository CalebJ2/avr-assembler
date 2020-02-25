.include "./m328Pdef.inc"

.equ ledMask = 0b00100000
.def zero = r1 ; r1 should always be zero
.def numLow = r16
.def numMid = r17
.def numUpper = r18
.def one = r19
.def temp = r20

    ldi one, 1 ; initialize our "one" register
    ldi temp, ledMask
    out DDRB, temp   ; Set led pin data direction to out
Increment:
    add numLow, one ; increment lower by one
    adc numMid, zero ; add zero + carry bit to mid
    adc numUpper, zero ; same for upper
    brcs TurnOn ; branch if upper carried/overflowed
    rjmp Increment ; else increment again
TurnOn:
    ldi temp, ledMask
    out PortB, temp  ; Set pin to high or low
    clr numLow
    clr numMid
    clr numUpper
Increment2:
    add numLow, one ; increment lower by one
    adc numMid, zero ; add zero + carry bit to mid
    adc numUpper, zero ; same for upper
    brcs TurnOff ; branch if upper carried/overflowed
    rjmp Increment2 ; else increment again
TurnOff:
    mov temp, zero
    out PortB, temp  ; Set pin to high or low
    rjmp Increment   ; start incrementing again