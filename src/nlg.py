import pdb, dateutil.parser

# Natural Language Generator
class nlg(object):

  def __init__(self):
    self.templates = {
      'request': 'Could you tell me what %s would work best for you?',
      'confirm': 'Could you confirm if you can make %s?',
      'reqalts': '',
      'finish': 'Thank you for helping me schedule your meeting. You will shortly receive a calendar invite for the meeting set up on %s at %s.',
      'req_org_loc': 'Thank you for helping me schedule your meeting. While I work with others, if you could you update me on the meeting location, that would be great.',
      'req_org_dt': ('Unfortunately, I was unable to find a slot in your calendar. Could you tell me a set of date and times that are convenient for you?'
                     '\n\nIf you have not done so already, you can integrate your calendar at https://autoscientist.com/login/google/ with us so I can automatically schedule your meetings.'
                    ),
      'req_org_add_loc': 'Also, could you tell me the location where to schedule this meeting?',

      'confirm_free_everyone': 'Would %s work for you?',
      'confirm_free_each_opening': 'It would be great if you could provide your preferences to me.',
      'confirm_free_each_following': '%s, would %s work for you?',

      '#greet': 'Hi %s,',
      '#greet_free': 'I am glad to coordinate scheduling your meeting.',
      '#hello': 'I am Sara and I will be helping with setting up your meeting.',
      '#thankyou': 'Thank you,\nSara.',
      '#allset': 'You are all set, have a great day!',
      '#replyback': 'If you would like to reschedule at anytime, you can reply me back.',
      '#space': ' ',
      '#para': '\n\n',
      '#qs': '?',
      '#add': '\n\nAlso, ',
    }


  def expand_list_natural(self, stringlist, appender='and'):
    filler = ''
    for i, item in enumerate(stringlist):
      filler += item
      if i==len(stringlist)-2:
        filler += ', %s ' % appender
      elif i<len(stringlist)-2:
        filler += ', '
    return filler


  def expand_dtstr_natural(self, dtstr):
    dtobj = dateutil.parser.parse(dtstr)
    return dtobj.strftime('%a %d %b %I:%M%p')

  def expand_dt_startend_natural(self, dt_startend):
    # dtobj_tup = (dateutil.parser.parse(dtstr_tup[0]), dateutil.parser.parse(dtstr_tup[1]))
    return dt_startend['start'].strftime('%a %d %b %I:%M%p') + ' to ' + dt_startend['end'].strftime('%I:%M%p')

  def greet_names(self, to_addrs, ppl):
    if len(to_addrs)<=4:
      names = []
      for email in to_addrs:
        names.append(ppl[email].first_name)
      namestr = self.expand_list_natural(names)
    else:
      namestr = 'everyone'
    return self.templates['#greet'] % namestr


  def expand_list_natural_2(self, stringlist):
    if len(stringlist)>1:
      return 'any of %s' % (self.expand_list_natural(stringlist, appender='or'))
    else:
      return list(stringlist)[0]


  def handler_confirm_free(self, fillers, e_act, ppl):
    if e_act['greet_free']:
      fillers.extend(['#greet_free', '#para'])

    user_proposals = {} # key: user_email, val: list of proposals
    for proposal in e_act['proposals']:
      for user_email in proposal['to_ask']:
        tmp = user_proposals.setdefault(user_email, list())
        tmp.append(proposal)

    all_users = set(user_proposals.keys())
    all_vals = set()
    ask_everyone = True
    for proposal in e_act['proposals']:
      if proposal['to_ask']!=all_users:
        ask_everyone = False
      all_vals.add(self.expand_dtstr_natural(proposal['val']))

    if ask_everyone:
      fillers.append(self.templates['confirm_free_everyone'] % self.expand_list_natural_2(all_vals))
    else:
      fillers.extend(['confirm_free_each_opening', '#para'])
      for user_email, proposal_list in user_proposals.iteritems():
        all_vals = set()
        for proposal in proposal_list:
          all_vals.add(self.expand_dtstr_natural(proposal['val']))
        fillers.append(self.templates['confirm_free_each_following'] % (ppl[user_email].first_name, self.expand_list_natural_2(all_vals)))
        fillers.extend('#para')


  def generate_response(self, e_act, ppl):
    # pdb.set_trace()
    fillers = [self.greet_names(e_act['to'], ppl)]
    fillers.append('#para')

    if e_act['act']=='finish':
      fillers.append(self.templates['finish'] % (self.expand_dt_startend_natural(e_act['dt']), e_act['loc']))
      fillers.extend(['#space', '#allset', '#para', '#replyback', '#para', '#thankyou',])

    if e_act['act']=='req_org_loc':
      fillers.append(self.templates['req_org_loc'])
      fillers.extend(['#para', '#thankyou',])

    if e_act['act']=='req_org_dt':
      fillers.append(self.templates['req_org_dt'])
      fillers.extend(['#para', '#thankyou',])

    if e_act['act']=='req_org_dt_loc':
      fillers.append(self.templates['req_org_dt'])
      fillers.extend(['#para', self.templates['req_org_add_loc']])
      fillers.extend(['#para', '#thankyou',])

    if e_act['act']=='confirm_free':
      self.handler_confirm_free(fillers, e_act, ppl)
      fillers.extend(['#para', '#thankyou',])


    return self.expand_response(fillers)


  def expand_response(self, fillers):
    # TODO: if last nonspace character was not '.', remove the capitalization in the following template being used
    response = ''
    for filler in fillers:
      if filler in self.templates:
        response += self.templates[filler]
      else:
        response += filler

    return response
