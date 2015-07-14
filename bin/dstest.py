#!/usr/bin/python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import sys, pdb, traceback
from math import log10
import numpy as np, re

from planus.src import ds

# Example test file for using an object of type ds()
def main():
  for i, line in enumerate(open('planus/data/sentences.txt', 'r')):
    testobj = ds.ds('tempid-'+str(i)) # For every new dialog, create an object of type ds() -- message ID (aka dialog ID) to be implemented soon.
    # print '\n\n'
    # print '%d, In: ' % i, line
    # print '\n'
    input_obj = get_input(line) # create the input object
    output_obj = testobj.take_turn(input_obj) # call take_turn, every time you get an email from the user
    # print '%d, Out: ' % i, output_obj['emails'][0]['body']
    print output_obj
    pdb.set_trace() # this is just for testing purposes to see if outputs seem ok.

# function that shows how to generate the input object for sending to ds.take_turn() starting from email_body
def get_input(email_body):
  input_obj = {
                'email': {
                            'from': {
                                      'email': 'example@gmail.com',
                                      'first_name': 'Krishna'
                                    },
                            'to': [
                                      {
                                        'email': '1@gmail.com',
                                        'first_name': 'Ananda'
                                      },
                                      {
                                        'email': '2@gmail.com',
                                        'first_name': 'Kelly'
                                      },
                                    ],
                            'body': 'main string of the email',
                          },
                'availability': {
                                  'datetime': [], # list of tuples of datetime objects
                                  'location': None, # some form of object, decide when we know more later
                                }
              }
  input_obj['email']['body'] = email_body
  return input_obj

if  __name__ =='__main__':
  try:
    main()
  except:
    typeval, value, tb = sys.exc_info()
    traceback.print_exc()
    pdb.post_mortem(tb)
