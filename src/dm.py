# Dialog Manager
import dateutil.parser, pdb
from planus.src.st import st

class dm(object):

  def __init__(self, dialog_id):
    self.st = st(dialog_id)

  def next_act(self, d_act):
    self.st.update_state(d_act)
    d_act_out = self.act_policy()
    self.st.add_action(d_act_out)
    return d_act_out


  def is_avail_busy_cal(self, dt):
    # for a given datetime value, checks for calendar availability for all busy users involved and returns True if everyone is free at that time
    busy_avail = True
    for email, user in self.st.meta['ppl'].iteritems():
      if not user.is_avail(dt):
        busy_avail = False
        break

    return busy_avail

  def propose_datetime(self):
    # if some datetime values have already been mentioned in the conversation through self.st.s['group'].datetime_avail
    #   choose the top 3 that are open in the calendars of all the busy users involved
    # if the total choices is < 3:
    #   look through the calendars of all the busy users, and add options to get to 3 choices
    # return whatever numbe of choices were proposed by the above

    # TODO: for now, proposals will be exact start datetime values for the meeting. this could be extended to do dateranges later

    # TODO: assumed that what this returns will later be added as a value to opt() and update its 'avail' set
    # returns a list of tuple of datetime objects

    # temp hard code
    dts = {}
    if len(self.st.dt_avail)>0:
      return None
      for k,v in self.st.dt_avail.iteritems():
        for elem in v:
          dtval = elem['value']
          dts
          if self.is_avail_busy_cal(dtval):
            vals.append({'val': dtval, })


    else:
      return None

  def act_policy(self):
    sums = self.summarize()
    d_act = {'meeting': None, 'acts': []}
    email_acts = []

    dts = sums['dt']['status']
    locs = sums['loc']['status']

    if dts=='finish' and locs=='finish':
      # A: everything is set
      d_act['meeting'] = {
        'dt': sums['dt']['val'],
        'loc': sums['loc']['val'],
        'to': self.st.all,
      }
      e_act = {
                'act': 'finish',
                'dt': sums['dt']['val'],
                'loc': sums['loc']['val'],
                'to': self.st.all - self.meta['busy'],
              }
      email_acts.append(e_act)

    if dts=='req_org' and locs=='req_org':
      # BC: could not find datetime from calendar or email, ask organizer
      e_act = {
                'act': 'req_org_dt_loc',
                'to': set([self.st.org]),
              }
      email_acts.append(e_act)
      d_act['acts'].append({'act': 'req_org', 'val': 'dt'})
      d_act['acts'].append({'act': 'req_org', 'val': 'loc'})

    if dts=='req_org' and locs in set(['finish', 'waiting']):
      # B: could not find datetime from calendar or email, ask organizer
      e_act = {
                'act': 'req_org_dt',
                'to': set([self.st.org]),
              }
      email_acts.append(e_act)
      d_act['acts'].append({'act': 'req_org', 'val': 'dt'})

    if dts in set(['new_users', 'waiting', 'confirm', 'finish']) and locs=='req_org':
      # C: ask organizer for location, meanwhile, do the necessary things with datetime
      e_act = {
                'act': 'req_org_loc',
                'to': set([self.st.org]),
              }
      email_acts.append(e_act)
      d_act['acts'].append({'act': 'req_org', 'val': 'loc'})

    if dts=='new_users' and locs in set(['finish', 'waiting']):
      # D: for each newly added user who is a busy user, send a separate email to them, only if necessary. for new free users, add them all to the ongoing thread
      raise NotImplementedError
      new_free = set()
      for useremail in sumst['dt']['to']:
        if useremail in self.meta['busy']:
          self.email_new_busy_users(email_acts, useremail)
        elif useremail in self.meta['free']:
          new_free.add(useremail)
        else:
          print 'new user neither in busy nor in free list'
          raise NotImplementedError

      if len(new_free)>0:
        e_act = {
                  'act': 'add_new_free_users',
                  'to': new_free,
                }
        email_acts.append(e_act)

    if dts=='confirm' and locs in set(['finish', 'waiting']):
      # E: confirmation can happen to free user thread or individual busy users
      raise NotImplementedError

    d_act['emails'] = email_acts
    return d_act


  def email_new_busy_users(self, email_acts, useremail):
    # TODO: this function should handle email to new busy users, after having checked their timings and so on
    e_act = {
              'act': 'tmp',
              'to': set([useremail]),
            }
    # email_acts.append(e_act)

  def summarize(self):
    sumst = {
      'dt': {
        'status': None,
        'val': None,
      },
      'loc': {
        'status': None,
        'val': None,
      },
    }

    # handle datetime
    if len(self.st.dt)>0:
      # check for the best agreed datetime values
      bestdt = self.st.dt[0]
      if bestdt['avail'] == self.st.all:
        # best datetime value is confirmed by everyone
        sumst['dt'] = {
          'status': 'finish',
          'val': bestdt['val'],
        }
      else:
        # if not confirmed by everyone - two possible situations: everyone informed of all values and we're waiting; or someone was added just now
        if len(self.st.meta['new'])>0:
          sumst['dt'] = {
            'status': 'new_users',
            'to': self.st.meta['new'],
          }
        else:
          sumst['dt'] = {
            'status': 'waiting',
          }
    else:
      # propose new datetime
      proposals = self.propose_datetime()
      if proposals is None:
        if self.st.asked['dt'] is False:
          sumst['dt'] = {
            'status': 'req_org',
          }
        else:
          sumst['dt'] = {
            'status': 'waiting',
          }
      else:
        sumst['dt'] = {
          'status': 'confirm',
          'val': proposals['vals'],
          'to': proposals['to_ask'],
        }

    # handle location
    if len(self.st.loc)>=1:
        sumst['loc'] = {
          'status': 'finish',
          'val': self.st.loc[0]['val'],
        }
    else:
      if self.st.asked['loc'] is False:
        sumst['loc'] = {
          'status': 'req_org',
        }
      else:
        sumst['loc'] = {
          'status': 'waiting',
        }

    return sumst
