import argparse
import warnings
import json
import re
import subprocess
from bitstring import BitArray, BitStream
from instruction import Instruction

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("sourceFile", help="The source file to assemble")
ap.add_argument("--upload", action="store_true", help="Whether to run the upload.sh script")
args = ap.parse_args()
asm = open(args.sourceFile, 'r')

program = []
macros = {}
labels = {}  # set by labels positions or .equ directives

schema = json.load(open('instructions.json', 'r'))

# flags
inComment = False
fileDepth = 0  # how many files we have recursed into
locationCounter = 1


def parseFile(filename):
    global locationCounter
    global fileDepth
    fileDepth += 1

    asm = open(filename, 'r')
    print("Parsing file '" + filename + "'")

    lineItr = asm.readline()
    asm.seek(0, 0)
    lineCounter = 0
    # read in the file and run the preprocessor
    while lineItr:
        lineItr = asm.readline()
        # copy line because we need to modify this without overwriting the iterator
        line = lineItr
        lineCounter += 1
        line = preprocess(line, lineCounter, filename)
        if not line:
            continue
        else:
            program.append(Instruction(line, lineCounter, filename, locationCounter))
            locationCounter += 1
    # only go past preprocess stage if this is the top level file
    if (fileDepth > 1):
        fileDepth -= 1
        return
    print("Preprocessing done")

    print("Assembling bytecode")
    for line in program:
        # get operation
        op = line.parseOp()
        if op is None:
            warnings.warn("No operation found on line " + str(line.lineNumber))
        else:
            # find instruction definition
            try:
                line.setDefinition(schema["instructions"][op])
            except KeyError:
                raise Exception(line.filename + "(" + str(line.lineNumber) + ") : Unsupported instruction '" + op + "'")
            line.setFormat(schema["instructionTypes"][line.definition["format"]])
        
        # evaluate numbers and labels
        try:
            line.evalFields(labels)
            line.generateBytecode()
        except:
            print(line.filename + "(" + str(line.lineNumber) + ") : Error :")
            raise

    fileDepth -= 1

# Modifies line. Returns true if it is an instruction
def preprocess(line, lineCounter, filename):
    global inComment
    global locationCounter
    # delete comments
    if inComment:
        # look for end of comment
        if re.search(r".*\*\/", line):
            inComment = False
            line = re.sub(r".*\*\/", "", line)
        else:  # still in comment
            line = ""
            return None
    # look for single line comments ; or // or /*  */
    line = re.sub(r";.*|\/\/.*|\/\*.*\*\/", "", line)
    # multiline comments
    if (re.search(r"\/\*", line)):
        line = re.sub(r"\/\*.*", "", line)
        inComment = True

    # trim whitespace and newlines
    line = re.sub(r"^\s+|\s+$", "", line)
    # exit if the line is blank now
    if (len(line) == 0):
        return None
    # check for stuff not supported by this yet
    if re.search(r"!|~|-|\*|\+|%|<<|>>|<|<=|>|==|!=|>=|&|\^|\||&&|\|\||\?", line):
        raise Exception(filename + "(" + str(line.lineNumber) + ") : Unsupported operator")

    # check for directives
    directive = re.match(r"(\#[a-zA-Z]+)|(\.[a-zA-Z]+)", line)
    if directive:
        if directive.group(2) == ".include":
            parseFile(re.match(r"\.include\s+\"([a-zA-Z0-9./-_]+)\"", line).group(1))
            return None
        elif directive.group(2) == ".equ":
            match = re.match(r"\.equ\s+(.*[^\s])\s*=\s*(.*[^\s])", line)
            setLabel(match.group(1), match.group(2), lineCounter, filename)
            return None
        elif directive.group(2) == ".def":
            match = re.match(r"\.def\s+(.*[^\s])\s*=\s*(r[1-3]?[0-9])", line)
            if not match:
                raise Exception(filename + "(" + str(line.lineNumber) + ") : directive doesn't match required format of .def <name> = <register>")
            else:
                setLabel(match.group(1), match.group(2), lineCounter, filename)
                return None
        else:
            print(filename + "(" + str(lineCounter) + ") : Warning : Ignoring unknown preprocessor directive '" + directive.group(0) + "'")
            return None

    # check for labels
    label = re.match(r"([a-zA-Z0-9]+):", line)
    if label:
        setLabel(label.group(1), locationCounter, lineCounter, filename)
        # label is recorded, remove it from the string
        line = re.sub(r"([a-zA-Z0-9]+):\s*", "", line)

    # make lower case so instructions and labels will be case insensitive
    return line.lower()

# Set a label if not already set
# Value can be the locationCounter or anything set by a .equ directive
# labels are case insensitive
def setLabel(label, value, lineCounter, filename):
    label = label.lower()
    if label in labels:
        raise Exception(filename + "(" + str(lineCounter) + ") : Redefinition of label '" + label + "'")
    else:
        labels[label] = value


def printPretty(sourceFilename):
    filename = sourceFilename + ".pretty.hex"
    print("Writing " + filename)
    # clear the file
    open(filename, "w").close()
    f = open(filename, "a")
    for line in program:
        f.write(line.source.ljust(20) + "0b" + line.bytecode.bin + "   0x" + line.bytecode.hex.upper() + "\n")

def writeHex(sourceFilename):
    filename = sourceFilename + ".hex"
    print("Writing " + filename)
    # clear the file
    open(filename, "w").close()
    f = open(filename, "a")
    # get program hex
    programHex = BitArray()
    for line in program:
        programHex.append(line.bytecode)
    # todo: make this split hex into 256 byte chunks if needed
    # until then just error
    if len(programHex)/8 > 256:
        raise Exception("Program exceeded 256 bytes")
    # place to put all the hex on this line
    hexLine = BitArray()
    # make 2 digit hex number with number of program bytes on this line
    dataSize = BitArray(uint=len(programHex)//8, length=8)
    hexLine.append(dataSize)
    # calculate start address. 4 digit hex number
    startAddress = BitArray(uint=0, length=16)
    hexLine.append(startAddress)
    # record type of data is 0x00. 2 digit hex number
    recordType = BitArray(uint=0, length=8)
    hexLine.append(recordType)
    # add program
    hexLine.append(programHex)
    # calculate checksum
    checksum = calculateChecksum(hexLine)
    hexLine.append(checksum)
    f.write(":" + hexLine.hex.upper() + "\n")
    # write line with EOF record type
    f.write(":00000001FF")

# add all bytes in BitArray together return the last byte of its twos complement
def calculateChecksum(bits):
    sum = 0
    for byte in bits.cut(8):
        sum += byte.int
    # take twos complement
    complementBits = BitArray(int=-sum, length=20)
    # get last 8 bits
    return complementBits[-8:]


parseFile(args.sourceFile)
filename = re.match(r"(.*)\.asm", args.sourceFile).group(1)
printPretty(filename)
writeHex(filename)
if args.upload:
    print("Running upload.sh")
    subprocess.call(["bash ./upload.sh " + filename + ".hex"], shell=True)
print("Done")
