import argparse
import exceptions
import warnings
import json
import re
from bitstring import BitArray, BitStream
from instruction import Instruction

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("sourceFile", help="The source file to assemble")
args = ap.parse_args()
asm = open(args.sourceFile, 'r')

program = []
macros = {}
labels = {} # set by labels positions or .equ directives

schema = json.load(open('instructions.json', 'r'))

# flags
inComment = False
fileDepth = 0 # how many files we have recursed into
locationCounter = 1

def parseFile(filename):
    global locationCounter
    global fileDepth
    fileDepth += 1

    asm = open(filename, 'r')
    print("Parsing file '" + filename + "'")

    lineItr = asm.readline()
    asm.seek(0,0)
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
            program.append(Instruction(line, lineCounter, filename))
            locationCounter += 1
    # only go past preprocess stage if this is the top level file
    if (fileDepth > 1):
        fileDepth -= 1
        return
    print("Preprocessed program:")
    print(program)

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
                raise Exception("Unsupported instruction '" + op + "' on line " + str(line.lineNumber) + " of '" + line.filename + "'")
            line.setFormat(schema["instructionTypes"][line.definition["format"]])
        
        # evaluate numbers and labels
        line.evalFields(labels)
        line.generateBytecode()
        print(line.bytecode)
    
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
        else: # still in comment
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
        raise Exception("Unsupported operator on line " + str(lineCounter) + " of '" + filename + "'")

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
        else:
            #warnings.warn("Unknown preprocessor directive " + directive.group(0) + " on line " + str(lineCounter) + " of '" + filename + "'")
            return None

    # check for labels
    label = re.match(r"([a-zA-Z0-9]+):", line)
    if label:
        setLabel(label.group(1), locationCounter, lineCounter, filename)
        # label is recorded, remove it from the string
        line = re.sub(r"([a-zA-Z0-9]+):\s*", "", line)
    
    return line

# Set a label if not already set
# Value can be the locationCounter or anything set by a .equ directive
def setLabel(label, value, lineCounter, filename):
    if label in labels:
        raise Exception("Redefinition or label '" + label + "' on line " + str(lineCounter) + " of '" + filename + "'")
    else:
        labels[label] = value

parseFile(args.sourceFile)