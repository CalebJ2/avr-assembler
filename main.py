import argparse
import exceptions
import warnings
import json
import re

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("sourceFile", help="The source file to assemble")
args = ap.parse_args()
asm = open(args.sourceFile, 'r')

preprocessed = []
macros = {}
labels = {} # set by labels positions or .equ directives

instr = json.load(open('instructions.json', 'r'))

def parseFile(filename):
    asm = open(filename, 'r')
    print("Parsing file '" + filename + "'")
    # flags
    inComment = False

    lineItr = asm.readline()
    asm.seek(0,0)
    locationCounter = 1
    lineCounter = 0
    while lineItr:
        lineItr = asm.readline()
        # need to modify this without messing up the iterator
        line = lineItr
        lineCounter += 1
        # ignore comments
        if inComment:
            # look for end of comment
            if re.search(r".*\*\/", line):
                inComment = False
                line = re.sub(r".*\*\/", "", line)
            else: # still in comment
                line = ""
                continue
        # look for single line comments ; or // or /*  */
        line = re.sub(r";.*|\/\/.*|\/\*.*\*\/", "", line)
        # multiline comments
        if (re.search(r"\/\*", line)):
            line = re.sub(r"\/\*.*", "", line)
            inComment = True
        # trim whitespace
        line = re.sub(r"^\s+|\s+$", "", line)
        # continue if the line is blank now
        if (len(line) == 0):
            continue
        # check for stuff not supported by this yet
        if re.search(r"!|~|-|\*|\+|%|<<|>>|<|<=|>|==|!=|>=|&|\^|\||&&|\|\||\?", line):
            raise Exception("Unsupported operator on line " + str(lineCounter) + " of '" + filename + "'")
        # warnings.warn("msg")

        # check for directives
        directive = re.match(r"(\#[a-zA-Z]+)|(\.[a-zA-Z]+)", line)
        if directive:
            if directive.group(2) == ".include":
                parseFile(re.match(r"\.include\s+\"([a-zA-Z0-9./]+)\"", line).group(1))
            elif directive.group(2) == ".equ":
                pass
            else:
                warnings.warn("Unknown preprocessor directive " + directive.group(0))
                continue

        # check for labels
        label = re.match(r"([a-zA-Z0-9]+):", line)
        if label:
            labels[label.group(1)] = locationCounter
            # label is recorded, remove it from the string

        # get first part of line
        part1 = re.match(r"([a-zA-Z]+)\s+", line)

        print(line)
        preprocessed.append(line)
        locationCounter += 1

parseFile(args.sourceFile)