# Natural Language Generator
class nlg(object):

  def __init__(self):
    self.templates = {
      'request': 'Could you tell me what %s would work best for you?',
      'confirm': 'Could you confirm if you can make %s?',
      'reqalts': '',
      'finish': 'Thank you for helping me schedule your meeting. You will shortly receive a calendar invite for the meeting set up on %s at %s.',
      'req_org_loc': 'Thank you for helping me schedule your meeting. While I work with others, if you could you update me on the meeting location, that would be great.',
      'req_org_dt_loc': ('Unfortunately, I was unable to find a slot in your calendar. Could you tell me a set of date and times that are convenient for you?'
                     '\n\nIf you have not done so already, you can integrate your calendar with us so I can automatically schedule your meetings.'
                    ),


      '#greet': 'Hi <name>,',
      '#hello': 'I am Sara and I will be helping with setting up your meeting.',
      '#thankyou': 'Thank you,\nSara.',
      '#allset': 'You are all set, have a great day!',
      '#replyback': 'If you would like to reschedule at anytime, you can reply me back.',
      '#space': ' ',
      '#para': '\n\n',
      '#qs': '?',
      '#add': '\n\nAlso, ',
    }

    self.slots_natural = {
      'location': 'location',
      'datetime': 'date and time',
    }

  def expand_list_natural(self, stringset, appender='and'):
    filler = ''
    for i, slot in enumerate(stringset):
      filler += self.slots_natural[slot]
      if i==len(stringset)-2:
        filler += ', %s ' % appender
      elif i<len(stringset)-2:
        filler += ', '
    return filler

  def expand_datetime_natural(self, dtobj_tup):
    return dtobj_tup[0].strftime('%a %d %b %I:%M%p') + ' to ' + dtobj_tup[1].strftime('%I:%M%p')

  def generate_response(self, d_act):
    if d_act['act']=='finish':
      fillers = ['#greet', '#para']
      fillers.append(self.templates['finish'] % (self.expand_datetime_natural(d_act['dt']), d_act['loc']))
      fillers.extend(['#space', '#allset', '#para', '#replyback', '#para', '#thankyou',])

    if d_act['act']=='req_org_loc':
      fillers = ['#greet', '#para']
      fillers.append(self.templates['req_org_loc'])
      fillers.extend(['#para', '#thankyou',])

    if d_act['act']=='req_org_dt_loc':
      fillers = ['#greet', '#para']
      fillers.append(self.templates['req_org_dt_loc'])
      fillers.extend(['#para', '#thankyou',])

    # if d_act['act']=='req_org_loc':
    #   fillers = ['#greet', '#para']
    #   fillers.append(self.templates['req_org_dt_loc'])
    #   fillers.extend(['#para', '#thankyou',])


    # if True:
      # fillers.append(self.templates['request'] % (self.expand_list_natural(d_act['slots_to_req'], appender='and')))
      # fillers.append(self.templates['confirm'] % (self.expand_list_natural(d_act['slots_to_req'], appender='or')))
      # fillers.extend(['#para', '#thankyou',])

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
