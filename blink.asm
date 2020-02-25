.include "./m328Pdef.inc"

.equ ledMask = 0b00100000
.def zero = r1
.def one = r14
.def temp = r15
.def numLow = r16
.def numMid = r17
.def numUpper = r18

    ldi one, 1 ; initialize our "one" register
    ldi zero, 0 ; initialize our "one" register
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
Decrement:
    sub numLow, one ; increment lower by one
    sbc numMid, zero ; sub zero + borrow bit to mid
    sbc numUpper, zero ; same for upper
    brcs TurnOff ; branch if upper tried to borrow
    rjmp Decrement ; else increment again
TurnOff:
    ldi temp, zero
    out PortB, temp  ; Set pin to high or low
    rjmp Increment   ; start incrementing again