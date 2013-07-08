#!/usr/bin/python
# -*- coding: utf-8

import sys          # system functions (like exit)
import time         # time functions
import re           # regular expressions
from os.path import getsize     # some useful functions for filenames
from pprint import pprint                           # nice print (used for debug)

# initialize global values
_inFile = None
_outFile = None
_verbose = 2

_FFcellsUMC = ['DFCM', 'DFCQM', 'DFCQRSM', 'DFCRSM', 'DFEM', 'DFEQM', 'DFEQRM', 'DFEQZRM', 'DFERM', 'DFEZRM', 'DFM', 'DFMM', 'DFMQM', 'DFQM', 'DFQRM', 'DFQRSM', 'DFQSM', 'DFQZRM', 'DFRM', 'DFRSM', 'DFSM', 'DFZRM']

# some regular expressions
_reModuleBegin = re.compile("`celldefine")
_reModuleName = re.compile("module [S]?(?P<type>[A-Z]+)[1248]{1}NM\$func\((?P<ports>[a-zA-Z0-9,_ ]+)\)")
_reEndOfHeader = re.compile("input notifier;")
_reCLKnegation = re.compile("not MGM_BG_\d{1}")
_reOutputBuf = re.compile("buf MGM_BG_\d{1}\([BINQ,]+\)")
_reOutputBufSig = re.compile("(IQ[N]?)")
_reModuleEnd = re.compile("`endcelldefine")



# Set input and output files
def setInputFile(filename):
    global _inFile
    _inFile = file(filename, 'r')
    if _verbose > 0:
        print "Input file:  " + filename

def setOutputFile(filename):
    global _outFile
    _outFile = file(filename, 'w')
    if _verbose > 0:
        print "Output file:  " + filename


def parseFile():
    global _inFile, _outFile, _nlines
    state = "idle"
    nlines = 0
    CLKname = ""

    for line in _inFile:
        nlines += 1

        # if nlines < 74000:
        #     continue
        # print state + "\t" + line.rstrip()

        if state == "idle":
            if _reModuleBegin.search(line):
                state = "begin"

        elif state == "begin":
            m = _reModuleName.search(line)
            if m and m.group('type') in _FFcellsUMC:
                state = "foundFF"
                ports = [x.strip() for x in m.group('ports').split(',')]
                if "CK" in ports:
                    CLKname = "CK"
                elif "CKB" in ports:
                    CLKname = "MGM_CLK"
            else:
                state = "idle"

        elif state == "foundFF":
            if _reEndOfHeader.search(line):
                if CLKname == "MGM_CLK":
                    state = "waitForCLK"
                else:
                    state = "insert"

        elif state == "waitForCLK":
            if _reCLKnegation.search(line):
                state = "insert"

        elif state == "insert":
            state = "waitForBuf"

        elif state == "waitForBuf":
            if _reModuleEnd.search(line):
                state = "idle"
            elif _reOutputBuf.search(line):
                state = "outputBuf"

        elif state == "outputBuf":
            state = "waitForBuf"

        # write output
        if state == "insert":  # additional stuff
            _outFile.write(line)
            _outFile.write("\n")
            _outFile.write("  // [SEU Insert {0}] Added SEU flag, set to 1 by nc_force\n".format(time.strftime('%Y-%m-%d')))
            _outFile.write("  reg SEU = 1'b0;\n")
            _outFile.write("  always @(posedge {0}) begin\n".format(CLKname))
            _outFile.write("    SEU <= 1'b0;\n")
            _outFile.write("  end\n")
            _outFile.write("\n")
            _outFile.write("  // [SEU Insert {0}] An intermediate signal which is switched if SEU is high\n".format(time.strftime('%Y-%m-%d')))
            _outFile.write("  wire IQ, IQ2, IQN, IQN2;\n")
            _outFile.write("  assign IQ2 = (SEU) ? ~IQ : IQ;\n")
            _outFile.write("  assign IQN2 = (SEU) ? ~IQN : IQN;\n")

        elif state == "outputBuf":
            _outFile.write("  // [SEU Insert {0}] Changed input for buffer\n".format(time.strftime('%Y-%m-%d')))
            _outFile.write("  //" + line)
            _outFile.write(_reOutputBufSig.sub("\g<1>2", line))

        else:
            _outFile.write(line)

        # if nlines > 74027:
        #     break


# How the program is intended to use
def printUsage():
    print "Usage: modifyUMClib.py <UMC_library_file> <modified_library>"
    print ""
    print "Parameter:"
    print "  UMC_library_file   The file of the unmodified UMC library, defining the"
    print "                     standard cells."
    print "  modified_library   The new library file which is created, including the"
    print "                     SEU flags inside the cells."
    sys.exit()


# The main program
def main():
    global _inFile, _outFile
    if len(sys.argv) != 3:
        printUsage()

    setInputFile(sys.argv[1])
    setOutputFile(sys.argv[2])

    parseFile()

    _inFile.close()
    _outFile.close()

    if _verbose > 0:
        print "File with {0} kB written.".format(getsize(_outFile.name)/1024)


if __name__ == '__main__':
    main()
