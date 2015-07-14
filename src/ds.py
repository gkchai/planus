#!/usr/bin/python
# -*- coding: utf-8 -*-
import pdb, datetime
from planus.src.nlu import nlu
from planus.src.dm import dm
from planus.src.nlg import nlg

# Dialog System
class ds(object):

  def __init__(self, dialog_id):
    self.dialog_id = dialog_id
    self.nlu = nlu()
    self.dm = dm(dialog_id)
    self.nlg = nlg()

  def take_turn(self, input_obj):
    utterance = input_obj['email']['body']
    d_act_in = input_obj['email']
    d_act_in['nlu'] = self.nlu.get_dialog_act(utterance)
    d_act_out = self.dm.next_act(d_act_in)
    emails = []
    for e_act in d_act_out['emails']:
      emails.append({'body': self.nlg.generate_response(e_act, d_act_out['ppl']), 'to': e_act['to']})
    self.save_dbs()
    return self.get_output(d_act_out, emails)

  def save_dbs(self):
    for email, person in self.dm.st.meta['ppl'].iteritems():
      person.save()
    self.dm.st.save()

  def get_output(self, d_act, emails):
    output = {
                'meeting': {
                              'dt': (None, None), # if everything is set, and meeting is ready to be added to calendar otherwise, None
                              'loc': '', # if everything is set, location to add to google calendar
                              'to': set(), # set of email ids
                            },
                'emails': [
                              {
                                'to': [], # set of email ids to cc during sending this email,
                                'body': '',
                              },
                          ],
             }
    output['meeting'] = d_act['meeting']
    output['emails'] = emails
    return output
