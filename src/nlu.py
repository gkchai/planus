import requests, pdb, urllib2
import json

# Natural Language Understanding unit
class nlu(object):

  def __init__(self):
    self.headers = {'Authorization': 'Bearer OUYQUGBHWOMQHP4Y47WWFBON6WR6I5WU'}

  def get_dialog_act(self, utterance):
    # url = 'https://api.wit.ai/message?v=20150628&q=lets%20meet%20sometime%20tomorrow'
    url = 'https://api.wit.ai/message?q='+urllib2.quote(utterance)
    response = requests.get(url, headers=self.headers)
    d_act = response.json()

    from planus.src.sara import *
    sara_debug(json.dumps(d_act))


    return d_act

######################################################################
# {'_text': 'Lets meet tomorrow 8 PM in McDonalds.\n',
#  'msg_id': '3227b5fa-700f-4fd4-b5f0-f7aab0f6a59e',
#  'outcomes': [{'_text': 'Lets meet tomorrow 8 PM in McDonalds.\n',
#    'confidence': 0.807,
#    'entities': {'datetime': [{'grain': 'hour',
#       'type': 'value',
#       'value': '2015-12-20T20:00:00.000-08:00',
#       'values': [{'grain': 'hour',
#         'type': 'value',
#         'value': '2015-12-20T20:00:00.000-08:00'}]}],
#     'location': [{'suggested': 'true', 'type': 'value', 'value': 'McDonalds'}],
#     'reminder': [{'entities': {'contact': [{'suggested': 'true',
#          'type': 'value',
#          'value': 'Lets'}]},
#       'suggested': 'true',
#       'type': 'value',
#       'value': 'Lets meet'}]},
#    'intent': 'Reminder'}]}
######################################################################
# {'_text': '19 Dec 08:00PM works for me',
#  'msg_id': '669ab9a1-2d6e-414b-8686-0cd4fb0e0146',
#  'outcomes': [{'_text': '19 Dec 08:00PM works for me',
#    'confidence': 0.802,
#    'entities': {'datetime': [{'grain': 'minute',
#       'type': 'value',
#       'value': '2015-12-19T20:00:00.000-08:00',
#       'values': [{'grain': 'minute',
#         'type': 'value',
#         'value': '2015-12-19T20:00:00.000-08:00'},
#        {'grain': 'minute',
#         'type': 'value',
#         'value': '2016-12-19T20:00:00.000-08:00'},
#        {'grain': 'minute',
#         'type': 'value',
#         'value': '2017-12-19T20:00:00.000-08:00'}]}],
#     'sentiment': [{'suggested': 'true', 'type': 'value', 'value': 'me'}]},
#    'intent': 'suggestion'}]}
#####################################################################
# {'_text': 'Yes, that works for me.\n',
#  'msg_id': '12e584cb-cdb8-4578-abf4-5771d055b1b9',
#  'outcomes': [{'_text': 'Yes, that works for me.\n',
#    'confidence': 0.945,
#    'entities': {},
#    'intent': 'suggestion'}]}
#####################################################################