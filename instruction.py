import re
import json

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
        for field in self.instrFormat["fields"]:
            # format provides named capture groups coresponding to their fields
            # see if the field is set by one of these
            try:
                groupValue = match.group(field["type"])
                # set fieldValue to value in the instruction
                self.fieldValues[field["type"]] = groupValue
            except IndexError:    
                # else it is probably the opcode or one of the default fields
                if field["type"] == "opcode":
                    self.fieldValues["opcode"] = self.definition["opcode"]
                elif field["type"] == "0":
                    self.fieldValues["0"] = "0b" + "0" * len(field["bits"])
                elif field["type"] == "1":
                    self.fieldValues["1"] = "0b" + "1" * len(field["bits"])
                else:
                    raise Exception("Unsupported field '" + field["type"] + "' on line " + str(self.lineNumber) + " of '" + self.filename + "'")
    # convert field labels and number strings to integers
    def evalFields(self, labels):
        for key, value in self.fieldValues.items():
            evaluated = False
            while not evaluated:
                # attempt to parse number
                try:
                    self.fieldValues[key] = int(value, 0)
                    evaluated = True
                except ValueError:
                    # probably a label
                    if value in labels:
                        self.fieldValues[key] = labels[value]
                        value = labels[value]
                    else:
                        raise Exception("Unknown value '" + value + "' on line " + str(self.lineNumber) + " of '" + self.filename + "'")
        print(self.fieldValues)