#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb, datetime
from src.nlu import nlu
from src.dm import dm
from src.nlg import nlg

# Dialog System
class ds(object):

  def __init__(self, dialog_id=None):
    self.nlu = nlu()
    self.dm = dm()
    self.nlg = nlg()

  def take_turn(self, input_obj):
    utterance = input_obj['email']['body']
    d_act_in = input_obj['email']
    d_act_in['nlu'] = self.nlu.get_dialog_act(utterance)
    d_act_out, email_acts = self.dm.next_act(d_act_in)
    pdb.set_trace()
    emails = []
    for email_act in emails_act:
      emails.append(self.nlg.generate_response(email_act))
    return self.get_output(d_act_out, emails)

  def get_output(self, d_act, emails):
    output = {
                'meeting': {
                              'datetime': (None, None), # if everything is set, and meeting is ready to be added to calendar otherwise, None
                              'location': '', # if everything is set, location to add to google calendar
                            },
                'emails': [
                              {
                                'to': to_addrs, # list of email ids to cc during sending this email,
                                'body': '',
                              },
                          ],
             }
    output['meeting'] = d_act
    output['emails'] = emails
    return output
