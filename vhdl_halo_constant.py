#!/usr/bin/python
# -*- coding: utf-8

# Import stuff
import sys

def PrintUsage():
    print 'Usage: ./vhdl_halo_constant <constant_name> <real_value>'
    print ''
    print '  <constant_name>: Your constant name.'
    print '  <real_value>:    The real value of the signal in bit format that should be changed.'
    print ''
    print '  Example:   ./vhdl_halo_constant TESTSIG 001'

# The main program
def main():
    if len(sys.argv) != 3:
        PrintUsage()
        sys.exit()

    constantName = sys.argv[1]
    realValue = int(sys.argv[2], 2)
    wordLength = len(sys.argv[2])

    for pos in range(0, wordLength):
        mask = 1 << pos
        haloValue = realValue ^ mask
        haloValueStr = str(bin(haloValue))[2:].zfill(wordLength)
        print 'constant {}_{} : state_type := "{}";'.format(constantName, pos, haloValueStr)


if __name__ == '__main__':
    main()
