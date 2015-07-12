import dateutil.parser, datetime, itertools
from src.person import group

# State Tracker
class st(object):
# TODO: agenda_entry can be used for title of the meeting. Or may be the busy + free guys' names

  def __init__(self):
    self.s = {
      'loc': [],
      'dt': [],
      # 'group': group(),
      'dt_avail': {},
      'org': '',
      'busyu': '',
      'freeu': '',
    } # , 'duration': opt(None)
    # self.s = {'loc': opt(None), 'dt': opt(None), 'group': group(None),} # , 'duration': opt(None)
    self.turns = []

  def set_organizer(self, useremail):
    self.organizer = useremail
    self.busy_emails.add(useremail)

  def update_dt_avail(self, useremail, availability):
    if useremail not in self.s['dt_avail']:
      self.s['dt_avail'][useremail] = []
    self.s['dt_avail'][useremail].append(availability)

  def update_state(self, d_act):
    info = {'d_act': d_act}
    if len(self.s['group'].people)==0:
      # this is the first time program is being called, so set the organizer for this meeting
      self.s['group'].set_organizer(d_act['from']['email'])
    users = d_act['to']+[d_act['from']]
    self.s['group'].update(users)
    # for slot in ['loc', 'dt']:
    #   self.s[slot].update_group(self.s['group'])

    if len(d_act['nlu']['outcomes'])>1:
      print 'More than 1 outcome! chk this case..'
      pdb.set_trace()

    #TODO: what happens when wit.ai's output is empty? handle the error cases
    for outcome in d_act['nlu']['outcomes']:
      # Ideally each location should also have an associated preference as should datetime
      if 'location' in outcome['entities']:
        for loc in outcome['entities']['location']:
          self.s['loc'].add(loc['value'], d_act['from']['email'], 'avail', len(self.turns))

      # TODO: ideally each object in the state's datetime list should have a preference. What if the person says in the subsequent conversation, that
        # "Oh, actually 6p might work better, but if not I can happily meet at 4. ". An extended version of preference could also be dispreference -
        # changing his mind. for instance, "actually, I can only do 6p, sorry."
      if 'datetime' in outcome['entities']:
        for dt in outcome['entities']['datetime']:
          for i, dt_interpret in enumerate(dt['values']):
            dtval = dateutil.parser.parse(dt_interpret['value'])
            wit_ai_bug = False
            if i>0:
              tmpdtval = dateutil.parser.parse(dt['values'][0]['value'])
              if dtval-tmpdtval > datetime.timedelta(days=365):
                wit_ai_bug = True
            if not wit_ai_bug:
              self.update_dt_avail(d_act['from']['email'], dt_interpret)
              # self.s['dt'].append(dt_interpret)
              # self.s['dt'].add(((dt_interpret['value'], ), user_email, preference)


            # in the following attempt, 'grain' information about datetime will be lost.
            # so we cannot distinguish betwn 'tomorrow' and 'tomorrow at 12am'
            # if dt_interpret['type'] == 'value':
            #   from_dt = dateutil.parser.parse(dt_interpret['value'])
            #   self.s['dt'].append((from_dt, ))
            # elif dt_interpret['type'] == 'interval':
            #   from_dt = dateutil.parser.parse(dt_interpret['from']['value'])
            #   to_dt = dateutil.parser.parse(dt_interpret['from']['value'])
            #   self.s['dt'].append((from_dt, to_dt))

      if 'duration' in outcome['entities']:
        for dur in outcome['entities']['duration']:
          self.s['duration'].add(dur, d_act['from']['email'], 'avail', len(self.turns))
          # self.s['duration'].append(dur)

    self.turns.append(info)

  def add_action(self, action_taken):
    last_turn = self.turns.pop()
    last_turn['action_taken'] = action_taken
    self.turns.append(last_turn)

    # TODO if a particular datetime was proposed by the policy in action_taken, add it to self.s['dt']
    # TODO update self.st.s['dt'][value]['asked'] here, and self.st.s['dt'].slot_asked and self.st.s['loc'].slot_asked
    # if suddenly by some chance


# Option handler
# TODO: remove value from self.values when removing from the pq() that is self.best_values
class opt(object):

  def __init__(self):
    # self.group = group
    self.values = dict()
    self.best_values = pq()
    self.asked_org = False

  # def update_group(self, group):
  #   self.group = group

  # preference can be 'avail' or 'tentative'
  def add(self, value, user_email, preference, turn):
    if value not in self.values:
      self.values[value] = {
        'avail': set(),
        # 'tentative': set(),
        'asked': set(),
        'turns_mentioned': [],
      }
    self.values[value][preference].add(user_email)
    if user_email in self.values[value]['asked']:
      self.values[value]['asked'].remove(user_email)
    self.best_values.add_task(value, self.get_priority(value))

  def get_priority(self, value):
    return (-len(self.values[value]['avail']))


# priority queue
from heapq import *
class pq(object):
  def __init__(self):
    self.pq = []                         # list of entries arranged in a heap
    self.entry_finder = {}               # mapping of tasks to entries
    self.REMOVED = '<removed-task>'      # placeholder for a removed task
    self.counter = itertools.count()     # unique sequence count

  def add_task(self, task, priority=0):
    'Add a new task or update the priority of an existing task'
    if task in self.entry_finder:
      remove_task(task)
    count = next(self.counter)
    entry = [priority, count, task]
    self.entry_finder[task] = entry
    heappush(self.pq, entry)

  def remove_task(self, task):
    'Mark an existing task as REMOVED.  Raise KeyError if not found.'
    entry = self.entry_finder.pop(task)
    entry[-1] = self.REMOVED

  def pop_task(self):
    'Remove and return the lowest priority task. Raise KeyError if empty.'
    while self.pq:
      priority, count, task = heappop(self.pq)
      if task is not self.REMOVED:
        del self.entry_finder[task]
        return task
    raise KeyError('pop from an empty priority queue')

  def peek_top(self):
    while self.pq:
      priority, count, task = heappop(self.pq)
      if task is not self.REMOVED:
        self.add_task(task, priority)
        return task
    raise KeyError('peek from an empty priority queue')

  def get_all_tasks(self):
    return self.entry_finder.keys()
