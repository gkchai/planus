#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb

# Dialog System
class person(object):

  def __init__(self, user):
    self.structure = {
      'email': user['email'],
      'first_name': user['first_name'],
      'calendar': [],                   # list of dict of 'start' and 'end' keys mapping to datetime objects
      'tenatively_booked': [],          # to be used by the DM to block the best datetime being discussed in current conversation
      'type': 'busy',                   # this value can either be 'busy' or 'free'
    }

class group(object):

  def __init__(self, users):
    self.id = ''
    self.people = {}
    self.datetime_avail = {}
    if users is not None:
      self.update(users)

  def update(self, users):
    for user in users:
      if user['email'] not in self.people:
        self.people[user['email']] = person(user)

  def update_avail(self, user_email, availability):
    if user_email not in self.datetime_avail:
      self.datetime_avail[user_email] = []
    self.datetime_avail[user_email].append(availability)
