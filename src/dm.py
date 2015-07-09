# Dialog Manager
import dateutil.parser
from src.st import st

class dm(object):

  def __init__(self):
    self.st = st()
    # self.s = {'location':[], 'datetime':[], 'duration':[]}


  def next_act(self, d_act):
    self.st.update_state(d_act)
    d_act_out = self.act_policy()
    self.st.add_action(d_act_out)
    return d_act_out

  def act_policy(self):
    # on a high level, this function should use ONLY self.st.s and then create a d_act_out which should be in turn processed by NLG
    # for location, first check for self.st.s['location'] if this is None, then directly ask
    # for datetime, first check for self.st.s['datetime'] if this is None, look into self.st.s['group'].datetime_avail -- this is a dictionary with keys as
      # user email Ids and values as list of wit.ai datetime objects, if this is also None, look into self.st.s['group'].people is a dictionary with keys as
      # user email Ids and values as person objects. So, look into self.st.s['group'].people['email_id'].structure['calender'] for each email_id and propose
      # a new time-window of some duration and create d_act_out

    # total number of people in thread = len(self.st.s['group'].people)
    # number of people agreed to a value in location = len(self.st.s['location'][value]['avail'])
    # number of people already asked about a value in location = len(self.st.s['location'][value]['asked'])
    # number of people agreed tentatively to a value in location = len(self.st.s['location'][value]['tentative'])

    if len(self.st.s['location'])==1 and len(self.st.s['datetime'])==1:
      d_act = {
                'act': 'finish',
                'slotvals': {
                              'location': self.st.s['location'][0],
                              'datetime': dateutil.parser.parse(self.st.s['datetime'][0]['value']),
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
