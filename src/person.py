#!/usr/bin/python
# -*- coding: utf-8 -*-

# Dialog System
class person(object):

  def __init__(self, user_email, first_name=None, utype=None):
    self.email = user_email
    self.first_name = first_name
    self.calendar = []                   # list of dict of 'start' and 'end' keys mapping to datetime objects
    self.tenatively_booked = []          # to be used by the DM to block the best datetime being discussed in current conversation
    self.type = utype                   # this value can either be 'busy' or 'free'
    self.active_threads = []

  def is_avail(self, dtval):
    return True

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
