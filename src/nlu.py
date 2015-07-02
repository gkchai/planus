import requests, pdb, urllib2
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
