#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests, pdb, urllib2, dateutil.parser, datetime
# from urllib2 import quote as urllib2_quote
# from dateutil import parser as dateutil_parser
# from datetime import datetime



# Natural Language Understanding unit
class nlu(object):

  def __init__(self):
    self.headers = {'Authorization': 'Bearer OUYQUGBHWOMQHP4Y47WWFBON6WR6I5WU'}

  def get_dialog_act(self, utterance):
    # url = 'https://api.wit.ai/message?v=20150628&q=lets%20meet%20sometime%20tomorrow'
    url = 'https://api.wit.ai/message?q='+urllib2.quote(utterance)
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
    if len(d_act['outcomes'])>1:
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
            dtval = dateutil.parser.parse(dt_interpret['value'])
            wit_ai_bug = False
            for tmpdt in self.s['datetime']:
              tmpdtval = dateutil.parser.parse(tmpdt['value'])
              if dtval-tmpdtval > datetime.timedelta(days=365):
                wit_ai_bug = True
            if not wit_ai_bug:
              self.s['datetime'].append(dt_interpret)

            # in the following attempt, 'grain' information about datetime will be lost.
            # so we cannot distinguish betwn 'tomorrow' and 'tomorrow at 12am'
            # if dt_interpret['type'] == 'value':
            #   from_dt = dateutil.parser.parse(dt_interpret['value'])
            #   self.s['datetime'].append((from_dt, ))
            # elif dt_interpret['type'] == 'interval':
            #   from_dt = dateutil.parser.parse(dt_interpret['from']['value'])
            #   to_dt = dateutil.parser.parse(dt_interpret['from']['value'])
            #   self.s['datetime'].append((from_dt, to_dt))

      if 'duration' in outcome['entities']:
        for dur in outcome['entities']['duration']:
          self.s['duration'].append(dur)

    self.turns.append(info)



# Natural Language Generator
class nlg(object):

  def __init__(self):
    self.templates = {
      'request': 'Could you tell me what %d would work best for you?',
      'confirm': '',
      'reqalts': '',
      'finish': 'Thank you for helping me schedule your meeting. You will shortly receive a calendar invite for the meeting set up on %s at %s.',

      '#greet': 'Hi you,',
      '#hello': 'I am Sara and I will be helping with setting up your meeting.',
      '#thankyou': 'Thank you,\nSara.',
      '#allset': 'You are all set, have a great day!',
      '#replyback': 'If you would like to reschedule at anytime, you can reply me back.',
      '#space': ' ',
      '#para': '\n\n',
      '#qs': '?',
    }

    self.slots_natural = {
      'location': 'location',
      'datetime': 'date and time',
    }

  def expand_list_natural(self, stringlist):
    filler = ''
    for i, slot in enumerate(stringlist):
      filler += self.slots_natural[slot]
      if i==len(stringlist)-2:
        filler += ', and '
      elif i<len(stringlist)-2:
        filler += ', '
    return filler

  def generate_response(self, d_act):
    fillers = ['#greet', '#para']
    if d_act['act'] == 'finish':
      fillers.append(self.templates[d_act['act']] % (d_act['slotvals']['datetime'], d_act['slotvals']['location']))
      fillers.extend(['#space', '#allset', '#para', '#replyback', '#para', '#thankyou',])

    elif d_act['act'] == 'request':
      fillers.append(self.templates[d_act['act']] % (self.expand_list_natural(d_act['slots'])))
      fillers.extend(['#para', '#thankyou',])

    response = ''
    for filler in fillers:
      if filler in self.templates:
        response += self.templates[filler]
      else:
        response += filler

    return response



# Dialog Manager
class dm(object):

  def __init__(self):
    self.st = st()
    self.s = {'location':[], 'datetime':[], 'duration':[]}


  def next_act(self, d_act):
    self.st.update_state(d_act)
    return self.act_policy()

  def act_policy(self):
    if len(self.st.s['location'])==1 and len(self.st.s['datetime'])==1:
      d_act = {
                'act': 'finish',
                'slotvals': {
                              'location': self.st.s['location'][0],
                              'datetime': self.st.s['datetime'][0]['value'],
                            },
                'to': 'email@email.com',
              }
    elif len(self.st.s['location'])==0 or len(self.st.s['datetime'])==0:
      d_act = {
                'act': 'request',
                'slots': []
              }
      for slot in ['location', 'datetime']:
        if len(self.st.s[slot])==0:
          d_act['slots'].append(slot)
    else:
      print 'too many locations or datetimes, not handled yet!'
      d_act = None
      pdb.set_trace()

    return d_act



# Dialog System
class ds(object):

  def __init__(self):
    self.nlu = nlu()
    self.dm = dm()
    self.nlg = nlg()

  def take_turn(self, utterance):
    d_act_in = self.nlu.get_dialog_act(utterance)
    d_act_out = self.dm.next_act(d_act_in)
    action = self.nlg.generate_response(d_act_out)
    return action


