# Natural Language Generator
class nlg(object):

  def __init__(self):
    self.templates = {
      'request': 'Could you tell me what %s would work best for you?',
      'confirm': '',
      'reqalts': '',
      'finish': 'Thank you for helping me schedule your meeting. You will shortly receive a calendar invite for the meeting set up on %s at %s.',

      '#greet': 'Hi <name>,',
      '#hello': 'I am Sara and I will be helping with setting up your meeting.',
      '#thankyou': 'Thank you,\nSara.',
      '#allset': 'You are all set, have a great day!',
      '#replyback': 'If you would like to reschedule at anytime, you can reply me back.',
      '#space': ' ',
      '#para': '\n\n',
      '#qs': '?',
    }

    self.slots_natural = {
      'location': 'location',
      'datetime': 'date and time',
    }

  def expand_list_natural(self, stringlist):
    filler = ''
    for i, slot in enumerate(stringlist):
      filler += self.slots_natural[slot]
      if i==len(stringlist)-2:
        filler += ', and '
      elif i<len(stringlist)-2:
        filler += ', '
    return filler

  def expand_datetime_natural(self, dt_obj):
    return dt_obj.strftime('%a %d %b %I:%M%p')

  def generate_response(self, d_act):
    fillers = ['#greet', '#para']
    if d_act['act'] == 'finish':
      fillers.append(self.templates[d_act['act']] % (self.expand_datetime_natural(d_act['slotvals']['datetime']), d_act['slotvals']['location']))
      fillers.extend(['#space', '#allset', '#para', '#replyback', '#para', '#thankyou',])

    elif d_act['act'] == 'request':
      fillers.append(self.templates[d_act['act']] % (self.expand_list_natural(d_act['slots'])))
      fillers.extend(['#para', '#thankyou',])

    response = ''
    for filler in fillers:
      if filler in self.templates:
        response += self.templates[filler]
      else:
        response += filler

    return response
