#!/usr/bin/python
# -*- coding: utf-8

# ------------------------------------------------------------------------------
#
#    Find flip flops in a synthesized verilog project
#   ---------------------------------------------------
#
#  Author:  André Goerres (andre.goerres@gmail.com)
#  Created: 2013-05-31
#
#  Description:
#
#  Revisions:
#    1.0 Initial revision
#
# ------------------------------------------------------------------------------

# Import stuff
import sys
import time
from os.path import basename, splitext
from pprint import pprint
from pyparsing import ParseException
from verilogParse import Verilog_BNF as verilogBNF


# configuration
_verbose = 1
_FFcells = ['DFF', 'DFFR', 'DFFS', 'DFFSR', 'SDFF', 'SDFFR', 'SDFFS', 'SDFFSR']


# global values
_inFile = None
_outFile = None
_topLevelName = ""
_verilogTokens = []
_FF = []
_instances = {}
_listOfModules = []
_verilogInstanceStrings = []


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

def setTopLevelName(name):
    global _topLevelName
    _topLevelName = name
    if _verbose > 0:
        print "Top Level Instance Name:  " + name


# Parse the file
def parseFile():
    # read content into memory
    global _inFile, _verilogTokens, _listOfModules
    if _verbose > 0:
        print "\nReading file {0} ...".format(_inFile.name)
    lines = _inFile.readlines()
    nlines = len(lines)
    _inFile.close()  # we don't need that anymore

    # convert text into tokens we can handle
    if _verbose > 0:
        print "  parse the input into memory ..."
    startTime = time.clock()
    lines = "".join(lines)
    try:
        _verilogTokens = verilogBNF().parseString(lines)
    except ParseException, err:
        print err.line
        print " "*(err.column-1) + "^"
        print err
        sys.exit()
    _listOfModules = [x[0][1] for x in _verilogTokens]
    stopTime = time.clock()
    totalTime = stopTime - startTime

    # some information output
    if _verbose > 0:
        print "  done converting {0} lines and {1} modules".format(nlines, len(_listOfModules))
        print "  time spent: {0:.2f} sec  ({1:.1f} lines/sec)\n".format(totalTime, nlines/totalTime)
    if _verbose > 2:
        print "Found the following modules:"
        pprint(_listOfModules, indent=2)
        print ""


# Search and find Flip Flops
def searchFlipFlops():
    global _instances

    if _verbose > 0:
        print "Searching for flip flops ..."
    for module in _verilogTokens:
        moduleName = module[0][1]
        for instance in module[1]:
            instanceType = instance[0]
            instanceName = instance[1][0][0]

            # check for FF cells
            if instanceType.split('_')[0] in _FFcells:
                _FF.append({
                    'type': instanceType,
                    'name': instanceName,
                    'module': moduleName
                })
                if _verbose > 1:
                    print "  found {0} for '{1}' in module '{2}'".format(instanceType, instanceName, moduleName)

            # found a module, put it into dict. for reverse searching
            if instanceType in _listOfModules:
                _instances[instanceType] = {
                    'name': instanceName,
                    'parent': moduleName
                }
                if _verbose > 2:
                    print "  instance '{0}' of type '{1}' is instantiated by '{2}'".format(instanceName, instanceType, moduleName)

    # some information output
    if _verbose > 0:
        print "  found {0} flip flops.".format(len(_FF))
    #pprint(_instances, indent=2)
    #pprint(_FF, indent=2)
    #print ""


# Take all the flip flops found and put them into a verilog instance list
def buildInstanceList():
    global _verilogInstanceStrings
    for FF in _FF:
        # basis of the string
        verilogString = "\{0} .i0.D".format(FF['name'])

        # include parent modules
        module = FF['module']
        while module in _instances.keys():
            verilogString = _instances[module]['name'] + "." + verilogString
            module = _instances[module]['parent']

        # add top level
        verilogString = ":" + _topLevelName + "." + verilogString
        _verilogInstanceStrings.append(verilogString)
        #print verilogString


def saveToOutput():
    global _outFile
    packageName = splitext(basename(_outFile.name))[0]

    # file header
    _outFile.write("-- Automatically generated VHDL file to import into testbench.\n")
    _outFile.write("--     generated on {0}\n".format(time.strftime('%x %X %Z')))
    _outFile.write("--\n")
    _outFile.write("-- To use this package, simply import it into your testbench:\n")
    _outFile.write("-- use work.{0}.all;\n".format(packageName))
    _outFile.write("--\n")
    _outFile.write("\n")

    # VHDL header
    _outFile.write('library ieee;\n')
    _outFile.write('use ieee.std_logic_1164.all;\n')
    _outFile.write('use ieee.numeric_std.all;\n')
    _outFile.write('\n')
    _outFile.write('package {0} is\n'.format(packageName))
    _outFile.write('  constant N_FLIPFLOPS : integer := {0};\n'.format(len(_FF)))
    _outFile.write('  function getFlipFlop( n : in integer ) return string;\n')
    _outFile.write('end;\n')
    _outFile.write('\n')

    # The return function with data
    _outFile.write('package body {0} is\n'.format(packageName))
    _outFile.write('  function getFlipFlop( n : in integer )\n')
    _outFile.write('  return string is\n')
    _outFile.write('  begin\n')
    _outFile.write('    case n is\n')
    i = 0
    for FF in _verilogInstanceStrings:
        _outFile.write('      when {0} => return "{1}";\n'.format(i, FF))
        i += 1
    _outFile.write('      when others => return "NOT FOUND";\n')
    _outFile.write('    end case;\n')
    _outFile.write('  end getFlipFlop;\n')
    _outFile.write('end package body;\n')

    _outFile.close()


# How the program is intended to use
def printUsage():
    print "Usage: fliflopfinder.py <verilog_project> <output_file> <toplevel_name>"
    print ""
    print "Parameter:"
    print "  output_file        Into which file should we save the result?"
    print "  verilog_project    The path to the verilog file conaining the project after"
    print "                     synthesis."
    print "  toplevel_name      The name used in the testbench to instantiate the top level."
    sys.exit()


# The main program
def main():
    if len(sys.argv) != 4:
        printUsage()

    setInputFile(sys.argv[1])
    setOutputFile(sys.argv[2])
    setTopLevelName(sys.argv[3])

    parseFile()
    searchFlipFlops()
    buildInstanceList()

    saveToOutput()

if __name__ == '__main__':
    main()
