.include "./m328Pdef.inc"

.equ ledMask = 0b00100000
.def zero = r1 ; r1 should always be zero
.def numLow = r16
.def numMid = r17
.def numUpper = r18
.def one = r19
.def temp = r20

    ldi one, 1 ; initialize our "one" register
    ldi temp, 0 ; make sure zero register is 0
    mov zero, temp
    ldi temp, ledMask
    out DDRB, temp   ; Set led pin data direction to out
    out PortB, temp  ; Set led pin to high
Increment:
    add numLow, one ; increment lower by one
    adc numMid, zero ; add zero + carry bit to mid
    adc numUpper, zero ; same for upper
    cpi numUpper, 0b00011111 ; half of full register
    breq TurnOn ; branch if numUpper is Same or Higher than value in previous instruction
    rjmp Increment ; else increment again
TurnOn:
    ldi temp, ledMask
    out PortB, temp  ; Set pin to high
    clr numLow
    clr numMid
    clr numUpper
Increment2:
    add numLow, one ; increment lower by one
    adc numMid, zero ; add zero + carry bit to mid
    adc numUpper, zero ; same for upper
    cpi numUpper, 0b00011111 ; half of full register
    breq TurnOff ; branch if numUpper is Same or Higher than value in previous instruction
    rjmp Increment2 ; else increment again
TurnOff:
    mov temp, zero
    out PortB, temp  ; Set pin to low
    clr numLow
    clr numMid
    clr numUpper
    rjmp Increment   ; start incrementing again