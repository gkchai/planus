# Dialog Manager
import dateutil.parser
from src.st import st

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
