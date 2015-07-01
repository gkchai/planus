#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import sys, pdb, traceback
from math import log10
import numpy as np, re

from src import ds
# timer = utils.runtimetracker()

# def parse_args():
#   parser = OptionParser(usage=" ", add_help_option=False)
#   parser.add_option("-h", "--help", action="help",
#       help="Show this help message and exit")
#   parser.add_option("-f", "--tabfname", type="str",
#       help="filename of data in tab sep format")
#   parser.add_option("-s", "--savefolder", type="str", default='results',
#       help="path to folder where results will be saved")

#   (opts, args) = parser.parse_args()
#   if len(args) != 0:
#     parser.print_help()
#     sys.exit(1)

#   return (opts, args)


def main():
  # opts, args = parse_args()
  for i, line in enumerate(open('data/sentences.txt', 'r')):
    testobj = ds.ds()
    print '\n\n'
    print '%d, In: ' % i, line
    print '\n'
    print '%d, Out: ' % i, testobj.take_turn(line)



if  __name__ =='__main__':
  try:
    main()
  except:
    typeval, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
