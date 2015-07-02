#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb, datetime
from src.nlu import nlu
from src.dm import dm
from src.nlg import nlg

# Dialog System
class ds(object):

  def __init__(self):
    self.nlu = nlu()
    self.dm = dm()
    self.nlg = nlg()

  def take_turn(self, input):
    utterance = input['email']['body']
    d_act_in = self.nlu.get_dialog_act(utterance)
    d_act_out = self.dm.next_act(d_act_in)
    email_body = self.nlg.generate_response(d_act_out)
    return self.get_output(d_act_out, email_body)

  def get_output(self, d_act, email_body):
    output = {
                'meeting': {
                              'datetime': (None, None), # if everything is set, and meeting is ready to be added to calendar otherwise, None
                              'location': '', # if everything is set, location to add to google calendar
                            },
                'emails': [
                              {
                                'to': '', # single string
                                'cc': [], # list of email ids to cc during sendint this email,
                                'body': '',
                              },
                          ],
             }
    output['emails'][0]['body'] = email_body
    if d_act['act'] == 'finish':
      output['meeting']['location'] = d_act['slotvals']['location']
      output['meeting']['datetime'] = (d_act['slotvals']['datetime'], d_act['slotvals']['datetime']+datetime.timedelta(hours=1))
    else:
      output['meeting'] = None
    return output
