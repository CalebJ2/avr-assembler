import re
import json
from bitstring import BitArray, BitStream


class Instruction:
    def __init__(self, source, lineNumber, filename, address):
        self.source = source  # instruction string
        self.lineNumber = lineNumber
        self.filename = filename
        self.address = address  # this instruction's location relative to start of program
        self.definition = None  # which instruction and format this is
        self.instrFormat = None  # the format schema defining the bytecode fields
        self.fieldValues = {}  # values to go in the fields
        self.bytecode = None  # string with bytecode in binary format
    # makes print(instruction) work better

    def __repr__(self):
        if self.bytecode:
            return self.bytecode
        elif self.source:
            return self.source
        else:
            return ""

    def parseOp(self):
        match = re.match(r"([a-zA-Z]+)\s+", self.source)
        if match:
            return match.group(1)
        else:
            return None

    def setDefinition(self, definition):
        self.definition = definition

    def setFormat(self, instrFormat):
        self.instrFormat = instrFormat
        # parse instruction using the format provided
        match = re.match(self.instrFormat["regex"], self.source)
        # fill in fieldValues
        for field, fieldInfo in self.instrFormat["fields"].items():
            # format provides named capture groups coresponding to their fields
            # see if the field is set by one of these
            try:
                groupValue = match.group(field)
                # set fieldValue to value in the instruction
                self.fieldValues[field] = groupValue
            except (IndexError, AttributeError):
                # else it is probably the opcode or one of the default fields
                if field == "opcode":
                    self.fieldValues["opcode"] = self.definition["opcode"]
                elif field == "0":
                    self.fieldValues["0"] = "0b" + "0" * len(fieldInfo["bits"])
                elif field == "1":
                    self.fieldValues["1"] = "0b" + "1" * len(fieldInfo["bits"])
                else:
                    raise Exception(self.filename + "(" + str(self.lineNumber) + ") : Unsupported field '" + field + "'")
    # convert field labels and number strings to integers
    def evalFields(self, labels):
        for field, value in self.fieldValues.items():
            evaluated = False
            while not evaluated:
                # attempt to parse number
                try:
                    self.fieldValues[field] = int(value, 0)
                    evaluated = True
                except (ValueError, TypeError):
                    # else check if it's a label
                    if value in labels:
                        self.fieldValues[field] = labels[value]
                        # if label is an int, we are done
                        if isinstance(labels[value], int):
                            evaluated = True
                        else:
                            # label is a string
                            value = labels[value]
                    # else check if it's a general purpose register
                    elif re.match(r"r[1-3]?[0-9]", value):
                        fieldLength = len(self.instrFormat["fields"][field]["bits"])
                        self.fieldValues[field] = self.evalGenReg(value, fieldLength)
                        evaluated = True
                    else:
                        raise Exception(self.filename + "(" + str(self.lineNumber) + ") : Unknown value '" + value + "'")
            # now that fieldValues[field] is set to a number, run any calculations
            if "formula" in self.instrFormat["fields"][field]:
                formula = self.instrFormat["fields"][field]["formula"]
                self.fieldValues[field] = eval(formula, {'__builtins__': {}}, {'fieldValue': self.fieldValues[field], 'PC': self.address})

    # register bit fields can be 3, 4, or 5 bits long
    # 3 bits -> r16-23
    # 4 bits -> r16-31
    # 5 bits -> r0-31
    def evalGenReg(self, register, fieldLength):
        number = int(re.match(r"r([1-3]?[0-9])", register).group(1))
        if fieldLength == 3 or fieldLength == 4:
            return number - 16
        else:
            return number

    # convert values to binary and put them into their places in the bytecode
    def generateBytecode(self):
        bytecode = BitArray("0x0000")
        # go through each field
        for field, fieldInfo in self.instrFormat["fields"].items():
            # convert int to binary
            length = len(fieldInfo["bits"])
            # pick whether to use signed or unsigned
            # I should have put this info in the json but it would have complicated things
            # it just means there is less error checking
            if self.fieldValues[field] < 0:
                fieldBits = BitArray(int=self.fieldValues[field], length=length)
            else:
                fieldBits = BitArray(uint=self.fieldValues[field], length=length)
            # but bits in their spots
            for i in range(len(fieldInfo["bits"])):
                # value, position
                # subtract position from 15 to convert addresses 0-15 to 15-0
                bytecode.set(fieldBits[i], 15-fieldInfo["bits"][i])
        # instructions must be little endian for some reason
        # swap the bytes
        tempByte = bytecode[0:8]
        bytecode[0:8] = bytecode[8:16]
        bytecode[8:16] = tempByte[0:8]
        self.bytecode = bytecode
