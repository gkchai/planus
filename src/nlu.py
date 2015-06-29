#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests, pdb
from urllib2 import quote as urllib2_quote
from dateutil import parser as dateutil_parser
from datetime import datetime


# Natural Language Understanding unit
class nlu(object):

  def __init__(self):
    self.headers = {'Authorization': 'Bearer OUYQUGBHWOMQHP4Y47WWFBON6WR6I5WU'}

  def get_dialog_act(self, string):
    # url = 'https://api.wit.ai/message?v=20150628&q=lets%20meet%20sometime%20tomorrow'
    url = 'https://api.wit.ai/message?q='+urllib2_quote(string)
    response = requests.get(url, headers=self.headers)
    d_act = response.json()
    return d_act



# State Tracker
class st(object):
# TODO: agenda_entry can be used for title of the meeting. Or may be the busy + free guys' names

  def __init__(self):
    self.s = {'location':[], 'datetime':[], 'duration':[]}
    self.turns = []

  def update_state(self, d_act):
    info = {'d_act': d_act}
    if len(r['outcomes'])>1:
      print 'More than 1 outcome! chk this case..'

    for outcome in d_act['outcomes']:
      # Ideally each location should also have an associated preference as should datetime
      if 'location' in outcome['entities']:
        for loc in outcome['entities']['location']:
          self.s['location'].append(loc['value'])

      # TODO: ideally each object in the state's datetime list should have a preference. What if the person says in the subsequent conversation, that
        # "Oh, actually 6p might work better, but if not I can happily meet at 4. ". An extended version of preference could also be dispreference -
        # changing his mind. for instance, "actually, I can only do 6p, sorry."
      if 'datetime' in outcome['entities']:
        for dt in outcome['entities']['datetime']:
          for dt_interpret in dt['values']:
            self.s['datetime'].append(dt_interpret)

            # in the following attempt, 'grain' information about datetime will be lost.
            # so we cannot distinguish betwn 'tomorrow' and 'tomorrow at 12am'
            # if dt_interpret['type'] == 'value':
            #   from_dt = dateutil_parser(dt_interpret['value'])
            #   self.s['datetime'].append((from_dt, ))
            # elif dt_interpret['type'] == 'interval':
            #   from_dt = dateutil_parser(dt_interpret['from']['value'])
            #   to_dt = dateutil_parser(dt_interpret['from']['value'])
            #   self.s['datetime'].append((from_dt, to_dt))

      if 'duration' in outcome['entities']:
        for dur in outcome['entities']['duration']:
          self.s['duration'].append(dur)

    self.turns.append(info)



# Dialog Manager
class dm(object):

  def __init__(self):
    self.s = {'location':[], 'datetime':[], 'duration':[]}



# Dialog System
class ds(object):

  def __init__(self):
    self.nlu = nlu()
    self.st = None # state tracker
    self.dm = dm()

  def act(self):
    pass
