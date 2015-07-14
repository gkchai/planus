#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb
from pymongo import MongoClient
client = MongoClient() # get a client
person_db = client.db.person # get the database, like a table in sql

# Dialog System
class person(object):

  def __init__(self, user_email, first_name=None, utype=None):
    dbrec = person_db.find_one({'_id': user_email})
    if dbrec is not None:
      # if present in db, read from db
      self.__dict__.update(dbrec)
      self.all_names = set(self.all_names)
    else:
      # if not in db, use defaults
      self.email = user_email
      self.first_name = first_name
      self.calendar = []                   # list of dict of 'start' and 'end' keys mapping to datetime objects
      self.tenatively_booked = []          # to be used by the DM to block the best datetime being discussed in current conversation
      self.type = utype                   # this value can either be 'busy' or 'free'
      self.active_threads = []
      self.all_names = set([first_name])

    # provided first_name and utype takes precendence over what is in db
    if first_name is not None:
      self.first_name = first_name
      if first_name not in self.all_names:
        self.all_names.add(first_name)
    if utype is not None:
      self.type = utype

    # if no first_name/utype are provided, use defaults
    if self.first_name is None:
      self.first_name = ''
    if self.type is None:
      self.type = 'free'


  def is_avail(self, dtval):
    return True

  def save(self):
    self.all_names = list(self.all_names)
    doc = self.__dict__
    doc['_id'] = doc['email']
    person_db.update({'_id': doc['_id']}, doc, upsert=True)

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
