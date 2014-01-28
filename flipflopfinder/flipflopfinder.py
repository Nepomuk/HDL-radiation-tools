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
#    1.1 UMC and IBM compatible
#
# ------------------------------------------------------------------------------

# Import stuff
import sys          # system functions (like exit)
import time         # time functions
import re           # regular expressions
from os.path import basename, splitext, getsize     # some useful functions for filenames
from pprint import pprint                           # nice print (used for debug)
from Cheetah.Template import Template               # template file


# verbose level
_verbose = 1

# template file as the basis for the output file
_templateFile = "flipflopfinder_template.vhd"

# which cells represent flip flops?
_FFcellsIBM = ['DFF', 'DFFR', 'DFFS', 'DFFSR', 'SDFF', 'SDFFR', 'SDFFS', 'SDFFSR']
_FFcellsUMC = ['DFCM', 'DFCQM', 'DFCQRSM', 'DFCRSM', 'DFEM', 'DFEQM', 'DFEQRM', 'DFEQZRM', 'DFERM', 'DFEZRM', 'DFM', 'DFMM', 'DFMQM', 'DFQM', 'DFQRM', 'DFQRSM', 'DFQSM', 'DFQZRM', 'DFRM', 'DFRSM', 'DFSM', 'DFZRM']
_FFcellsUMC_re = re.compile('[S]?(?P<type>[A-Z]+)[1248]{1}NM')


# initialize global values
_inFile = None
_outFile = None
_topLevelName = ""
_verilogTokens = []
_FF = []
_technology = "?"
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
    _verilogTokens = parseVerilog(lines)
    _listOfModules = [x[0] for x in _verilogTokens]
    stopTime = time.clock()
    totalTime = stopTime - startTime

    # some information output
    if _verbose > 0:
        if totalTime > 0:
            lineRate = nlines/totalTime
        else:
            lineRate = float("inf")
        print "  done converting {0} lines and {1} modules".format(nlines, len(_listOfModules))
        print "  time spent: {0:.2f} sec  ({1:.2e} lines/sec)\n".format(totalTime, lineRate)
    if _verbose > 2:
        print "Found the following modules:"
        pprint(_listOfModules, indent=2)
        print ""


def parseVerilog(lines):
    moduleStart_re = re.compile('^module (?P<module>\w+)\([\w, \n]+\);', re.MULTILINE)
    moduleEnd_re = re.compile('^endmodule$', re.MULTILINE)
    instance_re = re.compile('(?P<type>\w+) [\\\\]?(?P<name>[\w\[\]]+)\s?\([\w\s\\\\\[\]\(\){},.\']+\);', re.MULTILINE)
    moduleStartPos = 0
    moduleEndPos = 0
    moduleList = []

    while True:
        # determine the span of the module
        moduleStartMatch = moduleStart_re.search(lines, moduleEndPos)
        if not moduleStartMatch: break
        moduleStartPos = moduleStartMatch.end()
        moduleEndMatch = moduleEnd_re.search(lines, moduleStartPos)
        moduleEndPos = moduleEndMatch.start()

        # find the submodules
        instancesMatch = instance_re.findall(lines, moduleStartPos, moduleEndPos)

        # build a list
        module = [moduleStartMatch.group('module'), instancesMatch]
        moduleList.append(module)

    return moduleList



# Search and find Flip Flops
def searchFlipFlops():
    global _instances, _technology

    if _verbose > 0:
        print "Searching for flip flops ..."
    for module in _verilogTokens:
        moduleName = module[0]
        for instance in module[1]:
            instanceType = instance[0]
            instanceName = instance[1]
            UMCmatch = _FFcellsUMC_re.match(instanceType)

            # check for FF cells from IBM
            if (_technology == "IBM" or _technology == "?") and instanceType.split('_')[0] in _FFcellsIBM:
                _technology = "IBM"
                _FF.append({
                    'type': instanceType,
                    'name': instanceName,
                    'module': moduleName
                })
                if _verbose > 1:
                    print "  found {0} (IBM) for '{1}' in module '{2}'".format(instanceType, instanceName, moduleName)

            # check for FF cells from UMC
            elif (_technology == "UMC" or _technology == "?") and UMCmatch and UMCmatch.group('type') in _FFcellsUMC:
                _technology = "UMC"
                _FF.append({
                    'type': instanceType,
                    'name': instanceName,
                    'module': moduleName
                })
                if _verbose > 1:
                    print "  found {0} (UMC) for '{1}' in module '{2}'".format(instanceType, instanceName, moduleName)

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
        print "  found {0} flip flops.\n".format(len(_FF))
    #pprint(_instances, indent=2)
    #pprint(_FF, indent=2)
    #print ""


# Take all the flip flops found and put them into a verilog instance list
def buildInstanceList():
    global _verilogInstanceStrings
    for FF in _FF:
        # how is the inner part of the register called?
        if _technology == "UMC":
            innerFF = FF['type'] + "_inst"
        else:
            innerFF = "i0"

        # basis of the string
        if "[" in FF['name']:
            verilogString = "\{0} .{1}.D".format(FF['name'], innerFF)
        else:
            verilogString = "{0}.{1}.D".format(FF['name'], innerFF)

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

    if _verbose > 0:
        print "Writing output file ..."

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
