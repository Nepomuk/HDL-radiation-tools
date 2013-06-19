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
import sys          # system functions (like exit)
import time         # time functions
from os.path import basename, splitext, getsize     # some useful functions for filenames
from pprint import pprint                           # nice print (used for debug)
from pyparsing import ParseException                # parsing features
from verilogParse import Verilog_BNF as verilogBNF  # verilog parser
from Cheetah.Template import Template               # template file


# verbose level
_verbose = 1

# template file as the basis for the output file
_templateFile = "flipflopfinder_template.vhd"

# which cells represent flip flops?
_FFcells = ['DFF', 'DFFR', 'DFFS', 'DFFSR', 'SDFF', 'SDFFR', 'SDFFS', 'SDFFSR']


# initialize global values
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
        print "  parse the input into memory ... (might take a while)"
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
        if "[" in FF['name']:
            verilogString = "\{0} .i0.D".format(FF['name'])
        else:
            verilogString = "{0}.i0.D".format(FF['name'])

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
    t = Template(file=_templateFile)

    # fill the placeholders with meaning
    t.datetime = time.strftime('%x %X %Z')
    t.packageName = splitext(basename(_outFile.name))[0]
    t.nFF = len(_verilogInstanceStrings)
    t.flipflops = _verilogInstanceStrings
    t.flipflops_SEU = [ff[:-1] + "SEU" for ff in _verilogInstanceStrings]

    # write the file
    _outFile.write(str(t))
    _outFile.close()

    if _verbose > 0:
        print "File {0} with {1} kB written.".format(_outFile.name, getsize(_outFile.name)/1024)


# How the program is intended to use
def printUsage():
    print "Usage: fliflopfinder.py <verilog_project> <output_file> <toplevel_name>"
    print ""
    print "Parameter:"
    print "  output_file        Into which file should we save the result?"
    print "  verilog_project    The path to the verilog file conaining the project after"
    print "                     synthesis."
    print "  toplevel_name      The name used in the testbench to instantiate the top level."
    print ""
    print "For the output a template file is needed. Currently it is set to this file:"
    print "  '{0}'".format(_templateFile)
    print "Make sure that it exists. If you want to change this filename, see the configuration"
    print "section in this python script."
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
