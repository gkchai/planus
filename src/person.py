#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb

# Dialog System
class person(object):

  def __init__(self, user, utype=None):
    self.structure = {
      'email': user['email'],
      'first_name': user['first_name'],
      'calendar': [],                   # list of dict of 'start' and 'end' keys mapping to datetime objects
      'tenatively_booked': [],          # to be used by the DM to block the best datetime being discussed in current conversation
      'type': utype,                   # this value can either be 'busy' or 'free'
      'active_threads': [],
    }

class group(object):

  def __init__(self):
    self.id = ''
    self.people = {}
    self.organizer = ''
    self.busy_emails = set()
    # if users is not None:
    #   self.update(users)

  def update(self, users):
    for user in users:
      if user['email'] not in self.people:
        curr_user = person(user)
        if curr_user.structure['type'] == 'busy':
          self.busy_emails.add(user['email'])
        self.people[user['email']] = curr_user

