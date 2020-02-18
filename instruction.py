import re
import json
from bitstring import BitArray, BitStream

class Instruction:
    def __init__(self, source, lineNumber, filename):
        self.source = source # instruction string
        self.lineNumber = lineNumber
        self.filename = filename
        self.definition = None # which instruction and format this is
        self.instrFormat = None # the format schema defining the bytecode fields
        self.fieldValues = {} # values to go in the fields
        self.bytecode = None # string with bytecode in binary format
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
            except IndexError:    
                # else it is probably the opcode or one of the default fields
                if field == "opcode":
                    self.fieldValues["opcode"] = self.definition["opcode"]
                elif field == "0":
                    self.fieldValues["0"] = "0b" + "0" * len(fieldInfo["bits"])
                elif field == "1":
                    self.fieldValues["1"] = "0b" + "1" * len(fieldInfo["bits"])
                else:
                    raise Exception("Unsupported field '" + field + "' on line " + str(self.lineNumber) + " of '" + self.filename + "'")
    # convert field labels and number strings to integers
    def evalFields(self, labels):
        for field, value in self.fieldValues.items():
            evaluated = False
            while not evaluated:
                # attempt to parse number
                try:
                    self.fieldValues[field] = int(value, 0)
                    evaluated = True
                except ValueError:
                    # maybe a label
                    if value in labels:
                        self.fieldValues[field] = labels[value]
                        value = labels[value]
                    # maybe a general purpose register
                    elif re.match(r"r[1-3]?[0-9]", value):
                        fieldLength = len(self.instrFormat["fields"][field]["bits"])
                        value = self.evalGenReg(value, fieldLength)
                    else:
                        raise Exception("Unknown value '" + value + "' on line " + str(self.lineNumber) + " of '" + self.filename + "'")
        print(self.fieldValues)

    # register bit fields can be 3, 4, or 5 bits long
    # 3 bits -> r16-23
    # 4 bits -> r16-31
    # 5 bits -> r0-31
    def evalGenReg(self, register, fieldLength):
        number = re.match(r"r([1-3]?[0-9])", register).group(1)
        if fieldLength == 3 or fieldLength == 4:
            return number - 16
        else:
            return number

    def generateBytecode(self):
        bytecode = BitArray("0x0000")
        # go through each field
        for field, fieldInfo in self.instrFormat["fields"].items():
            # convert int to binary
            length = len(fieldInfo["bits"])
            fieldBits = BitArray(uint=self.fieldValues[field], length=length)
            print(fieldBits)
            # but bits in their spots
            for i in range(len(fieldInfo["bits"])):
                # value, position
                bytecode.set(fieldBits[i], fieldInfo["bits"][i])
        self.bytecode = bytecode
        return self.bytecode
