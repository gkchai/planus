#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb

# Dialog System
class person(object):

  def __init__(self, email):
    self.email = email
    self.calendar = [] # list of tuple of datetime objects - tuple represents
    self.tenatively_booked = [] # to be used by the DM to block the best datetime being discussed in current conversation

