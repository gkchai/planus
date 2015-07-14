import dateutil.parser, datetime, heapq, itertools, pdb
from planus.src.person import person
from pymongo import MongoClient
client = MongoClient() # get a client
dialog_db = client.db.dialog # get the database, like a table in sql

def instance_helper(v):
  if isinstance(v, list):
    v2 = []
    for elem in v:
      v2.append(instance_helper(elem))
    return v2
  elif isinstance(v, dict):
    return convert_sets_lists(v)
  elif isinstance(v, set):
    return list(v)
  else:
    return v

def convert_sets_lists(d):
  d2 = {}
  for k,v in d.iteritems():
    d2[k] = instance_helper(v)
  return d2


def pack_dotfields(d):
  d2 = []
  for k,v in d.iteritems():
    d2.append({'k':k, 'v':v})
  return d2

def unpack_dotfields(d):
  d2 = {}
  for elem in d:
    d2[elem['k']] = elem['v']
  return d2


# State Tracker
class st(object):
# TODO: agenda_entry can be used for title of the meeting. Or may be the busy + free guys' names

  def __init__(self, dialog_id):
    dbrec = dialog_db.find_one({'_id': dialog_id})
    if dbrec is not None:
      # if present in db, read from db
      self.__dict__.update(dbrec)
      self.all = set(self.all)
      for elem in self.dt:
        elem['avail'] = set(elem['avail'])
        elem['asked'] = set(elem['asked'])
      self.dt_avail = unpack_dotfields(self.dt_avail)
    else:
      # if not in db, use defaults
      self.dialog_id = dialog_id
      self.dt = [] # list of dicts {'val': value, 'avail': [list of emails], 'asked': [list of emails]}
      self.loc = [] # list of dicts {'val': value, 'from': email, 'turn': turn_mentioned}
      self.dur = [] # similar to self.loc
      self.asked = {'loc': False, 'dt': False}
      self.dt_avail = {}
      self.org = ''
      self.all = set()
      self.greeted_free = False # tracks if the free users have been greeted in the first ever email
      self.turns = []

    self.meta = {
      'ppl': {},
      'new': set(),
      'busy': set(),
      'free': set(),
    }


  def save(self):
    self.all = list(self.all)
    for elem in self.dt:
      elem['avail'] = list(elem['avail'])
      elem['asked'] = list(elem['asked'])
    del self.meta
    # write to db
    doc = self.__dict__
    doc['_id'] = doc['dialog_id']
    doc = convert_sets_lists(doc)
    doc['dt_avail'] = pack_dotfields(doc['dt_avail'])
    doc['turns'][-1] = 'tmp'
    dialog_db.update({'_id': doc['_id']}, doc, upsert=True)


  def update_opts(self):
    self.loc.sort(lambda x: x['turn'], reverse=True)
    self.dt.sort(lambda x: len(x['avail']), reverse=True)

  def update_users(self, users):
    # update ppl, free, busy from current database
    for user in users:
      if user['email'] not in self.meta['ppl']:
        self.meta['ppl'][user['email']] = person(user['email'], user['first_name'])
      if user['email'] not in self.all:
        self.all.add(user['email'])
        self.meta['new'].add(user['email'])

    self.meta['busy'] = set()
    self.meta['free'] = set()
    for user_email in self.all:
      if user_email not in self.meta['ppl']:
        p = person(user_email)
      else:
        p = self.meta['ppl'][user_email]
      if p.type == 'busy':
        self.meta['busy'].add(user_email)
      elif p.type == 'free':
        self.meta['free'].add(user_email)


  def update_dt_avail(self, user_email, availability):
    if user_email not in self.dt_avail:
      self.dt_avail[user_email] = []
    self.dt_avail[user_email].append(availability)

  def update_state(self, d_act):
    info = {'d_act': d_act}
    self.meta['ppl'] = {}
    if len(self.all)==0:
      # this is the first time program is being called, so set the organizer for this meeting
      self.org = d_act['from']['email']
      self.meta['busy'].add(self.org)
      self.meta['ppl'][self.org] = person(self.org, d_act['from']['first_name'], 'busy')
    users = d_act['to']+[d_act['from']]
    self.update_users(users)

    if len(d_act['nlu']['outcomes'])>1:
      print 'More than 1 outcome! chk this case..'
      pdb.set_trace()

    #TODO: what happens when wit.ai's output is empty? handle the error cases
    for outcome in d_act['nlu']['outcomes']:
      # Ideally each location should also have an associated preference as should datetime
      if 'location' in outcome['entities']:
        for loc in outcome['entities']['location']:
          self.loc.append({'val': loc['value'], 'from': d_act['from']['email'], 'turn': len(self.turns)})

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
          self.dur.append({'val': dur, 'from': d_act['from']['email'], 'turn': len(self.turns)})
          # self.s['duration'].append(dur)

    self.turns.append(info)

  def add_action(self, d_act_out):
    last_turn = self.turns.pop()
    last_turn['d_act_out'] = {}
    for k,v in d_act_out.iteritems():
      if k!='ppl':
        last_turn['d_act_out'][k] = d_act_out[k]
    self.turns.append(last_turn)

    # TODO if a particular datetime was proposed by the policy in d_act_out, add it to self.s['dt']
    # TODO update self.st.s['dt'][value]['asked'] here, and self.st.s['dt'].slot_asked and self.st.s['loc'].slot_asked
    # if suddenly by some chance

    for elem in d_act_out['acts']:
      # update state with slots asked in this turn
      if elem['act']=='req_org':
        self.asked[elem['val']] = True

      # update with free users asked to confirm this turn
      if elem['act']=='confirm_free':
        self.greeted_free = True # first greeting to free users has been just established through this email
        proposals = elem['proposals'] # list of dict, {'val': dtval, 'avail': set(emails), 'to_ask': set(emails)}
        for proposal in proposals:
          to_update = None
          for dtdict in self.dt:
            if proposal['val']==dtdict['val']:
              to_update = dtdict
              break
          if to_update is None:
            to_update = {'val': proposal['val'], 'avail': set(), 'asked': set()}

          to_update['asked'] = to_update['asked'].union(proposal['to_ask'])
          to_update['avail'] = to_update['avail'].union(proposal['avail'])



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
