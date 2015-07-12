# Dialog Manager
import dateutil.parser, pdb
from src.st import st

# #location
# # if busy guy mentions
#   done
# else:
#   if no one mentions:
#     ask everyone
#   else:


class dm(object):

  def __init__(self):
    self.st = st()
    # self.s = {'location':[], 'dt':[], 'duration':[]}


  def next_act(self, d_act):
    self.st.update_state(d_act)
    pdb.set_trace()
    d_act_out = self.act_policy()
    self.st.add_action(d_act_out)
    return d_act_out

  def update_users(self):
    self.group_users = set(self.st.s['group'].people.keys())
    self.busy_users = self.st.s['group'].busy_emails
    self.organizer = self.st.s['group'].organizer
    self.free_users = (self.group_users - self.busy_users) - set([self.organizer])

  def propose_datetime(self):
    # if some datetime values have already been mentioned in the conversation through self.st.s['group'].datetime_avail
    #   choose the top 3 that are open in the calendars of all the busy users involved
    # if the total choices is < 3:
    #   look through the calendars of all the busy users, and add options to get to 3 choices
    # return whatever numbe of choices were proposed by the above

    # TODO: for now, proposals will be exact start datetime values for the meeting. this could be extended to do dateranges later

    # TODO: assumed that what this returns will later be added as a value to opt() and update its 'avail' set
    # returns a list of tuple of datetime objects
    if self.st.s['group'].organizer
    return None

  def act_policy(self):
    self.update_users()
    group_users = set(self.st.s['group'].people.keys())
    busy_users = self.st.s['group'].busy_emails
    organizer = self.st.s['group'].organizer
    free_users = (group_users - busy_users) - set([organizer])
    sums = self.summarize_state()
    d_act = None
    email_acts = []

    dts = sums['dt']['status']
    locs = sums['loc']['status']
    if dts=='finish' and locs=='finish':
      # A: everything is set
      d_act = {
        'dt': sums['dt']['val'],
        'loc': sums['loc']['val'],
      }
      e_act = {
                'act': 'finish',
                'dt': sums['dt']['val'],
                'loc': sums['loc']['val'],
                'to': group_emails - busy_users,
              }
      email_acts.append(e_act)

    # if dts=='finish' and locs=='request_org':
    #   # B: datetime set but not location; ask organizer for location
    #   e_act = {
    #             'act': 'req_loc',
    #             'dt': sums['dt']['val'],
    #             'to': set([organizer]),
    #           }
    #   email_acts.append(e_act)

    if dts=='request_org' and locs=='request_org':
      # C: could not find datetime from calendar or email, ask organizer
      e_act = {
                'act': 'req_dt_loc',
                'to': set([organizer]),
              }
      email_acts.append(e_act)

    if dts in set(['new_users', 'waiting', 'confirm', 'finish']) and locs=='request_org':
      # D: ask organizer for location, meanwhile, do the necessary things with datetime
      e_act = {
                'act': 'req_loc',
                'to': set([organizer]),
              }
      email_acts.append(e_act)

    if dts=='waiting':
      pass

    if dts=='new_users':
      # for each newly added user who is a busy user, send a separate email to them, only if necessary. for new free users, add them all to the ongoing thread
      new_free = set()
      for useremail in sumst['dt']['to']:
        if useremail in busy_users:
          self.email_new_busy_users(email_acts, useremail)
        else:
          new_free.add(useremail)

      if len(new_free)>0:
        e_act = {
                  'act': 'add_new_free_users',
                  'to': new_free,
                }
        email_acts.append(e_act)

    if dts=='confirm':
      # confirmation can happen to free user thread or individual busy users
      raise NotImplementedError

    return (d_act, email_acts)


  def email_new_busy_users(self, email_acts, useremail):
    # TODO: this function should handle email to new busy users, after having checked their timings and so on
    e_act = {
              'act': 'tmp',
              'to': set([useremail]),
            }
    # email_acts.append(e_act)

  def summarize_state(self):
    group_users = set(self.st.s['group'].people.keys())
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
    try:
      # check for the best agreed datetime values
      slotopts = self.st.s['dt']
      bestval = slotopts.best_values.peek_top()
      bestval_stats = slotopts.values[bestval]
      pdb.set_trace()
      if bestval_stats['avail'] == group_users:
        # best datetime value is confirmed by everyone
        sumst['dt'] = {
          'status': 'finish',
          'val': bestval,
          # 'to': free_users,
        }
      else:
        # if not confirmed by everyone - two possible situations: everyone informed of all values and we're waiting; or someone was added just now
        new_users = set()
        for val, valstats in slotopts.values.iteritems():
          to_ask = group_users - (valstats['avail'] | valstats['asked'])
          if len(to_ask)==0:
            # in this state, everyone has been informed about the value val, and Sara is waiting for at least one of the responses
            pass
          else:
            # in this state, someone was just added into our conversation who haven't been informed before about the options
            new_users = new_users.union(to_ask)
        if len(new_users)>0:
          sumst['dt'] = {
            'status': 'new_users',
            'to': new_users,
          }
        else:
          sumst['dt'] = {
            'status': 'waiting',
          }
    except KeyError:
      pdb.set_trace()
      # propose new datetime
      proposals = self.propose_datetime()
      if proposals is None:
        if self.st.s['dt'].asked_org is False:
          sumst['dt'] = {
            'status': 'request_org',
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
    all_locations = self.st.s['loc'].values.keys()
    if len(all_locations)==1:
        sumst['loc'] = {
          'status': 'finish',
          'val': all_locations[0],
        }
    elif len(all_locations)>1:
      most_recent_location = ''
      most_recent_turn = -1
      for loc in all_locations:
        last_turn_mentioned = self.st.s['loc'].values[loc]['turns_mentioned'][-1]
        if last_turn_mentioned > most_recent_turn:
          most_recent_location = loc
          most_recent_turn = last_turn_mentioned
        sumst['loc'] = {
          'status': 'finish',
          'val': most_recent_location,
        }
    else:
      if self.st.s['loc'].asked_org is False:
        sumst['loc'] = {
          'status': 'request_org',
        }
      else:
        sumst['loc'] = {
          'status': 'waiting',
        }

    return sumst
