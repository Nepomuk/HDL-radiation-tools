#!/usr/bin/python
# -*- coding: utf-8

# ------------------------------------------------------------------------------
#
#    Hamming Code Table Generator
#   ------------------------------
#
#  Author:  André Goerres (andre.goerres@gmail.com)
#  Created: 2013-04-17
#
#  Description: A simple script generating a Hamming Code translation table. You
#               give it the length of the signal words and it returns you the
#               table.
#
#  Revisions:
#    1.0 Initial revision
#
# ------------------------------------------------------------------------------

# Import stuff
import sys

# default values
nSignalBits = 4
nParityBits = 3
nTotalBits = 7


def HamCode(signal):
    # set a copy of the signal bits
    encodedSignal = MoveSignalBits(signal)

    # calculate the parity bits
    encodedSignal = CalculateParityBits(encodedSignal)

    return encodedSignal


# move the signal bits to the corresponding positions in the encoded signal
def MoveSignalBits(sig):
    sigEncoded = 0
    pos = 2  # the first two bits are parity bits
    while sig > 0:
        lastBit = sig & 1
        sigEncoded += lastBit << pos

        # position where to put the next signal bit
        pos += 1
        if isParityPosition(pos):
            pos += 1

        # shift the signal for the next round
        sig = sig >> 1

    return sigEncoded


def CalculateParityBits(sig):
    encodedSig = sig
    for pBit in range(0, nParityBits):
        parity = 0
        posMask = 1 << pBit
        startAt = 2**pBit + 1
        for pos in range(startAt, nTotalBits+1):
            # only consider the current position, when the matching bit is set
            if ((pos) & posMask) == 0:
                continue

            valueAtPos = (sig >> pos-1) & 1
            parity = parity ^ valueAtPos
            #print str(pos) + ": yep  -  " + str(bin(sig))[2:].zfill(nTotalBits) + " " + str((sig >> pos-1) & 1)

        # include the parity bit into the signal
        parityPos = 2**pBit - 1
        encodedSig = encodedSig + (parity << parityPos)
    return encodedSig


# if the position is a power of two, it is a parity position
def isParityPosition(pos):
    pos += 1
    return pos != 0 and ((pos & (pos - 1)) == 0)


# how many parity bits do we need?
def ParityBits():
    for m in range(2, nSignalBits):
        sigLenMax = 2**m - m - 1
        if (sigLenMax >= nSignalBits):
            return m


# How the program is intended to use
def printUsage():
    print "Usage: hamming_table.py [<signal_length>]"
    print ""
    print "Options:"
    print "  signal_length   default: 4"


# The main program
def main():
    global nSignalBits, nParityBits, nTotalBits

    if len(sys.argv) > 1 and int(sys.argv[1]) > 0 and int(sys.argv[1]) <= 10:
        nSignalBits = int(sys.argv[1])
        nParityBits = ParityBits()
        nTotalBits = nSignalBits + nParityBits

    print "Printing table for Ham(" + str(nTotalBits) + "," + str(nSignalBits) + "):"

    for signal in range(0, 2**nSignalBits):
        sigBin = str(bin(signal))[2:].zfill(nSignalBits)
        hamBin = str(bin(HamCode(signal)))[2:].zfill(nTotalBits)
        print sigBin + "   " + hamBin


if __name__ == '__main__':
    main()
