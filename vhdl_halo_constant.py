#!/usr/bin/python
# -*- coding: utf-8

# Import stuff
import sys


# The main program
def main():
    if len(sys.argv) != 3:
        sys.exit()

    constantName = sys.argv[1]
    realValue = int(sys.argv[2], 2)
    wordLength = len(sys.argv[2])

    for pos in range(0, wordLength):
        mask = 1 << pos
        haloValue = realValue ^ mask
        haloValueStr = str(bin(haloValue))[2:].zfill(wordLength)
        print 'constant {}_{} := "{}";'.format(constantName, pos, haloValueStr)


if __name__ == '__main__':
    main()
