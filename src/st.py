import dateutil.parser, datetime

# State Tracker
class st(object):
# TODO: agenda_entry can be used for title of the meeting. Or may be the busy + free guys' names

  def __init__(self):
    self.s = {'location':[], 'datetime':[], 'duration':[]}
    self.turns = []

  def update_state(self, d_act):
    info = {'d_act': d_act}
    if len(d_act['outcomes'])>1:
      print 'More than 1 outcome! chk this case..'

    for outcome in d_act['outcomes']:
      # Ideally each location should also have an associated preference as should datetime
      if 'location' in outcome['entities']:
        for loc in outcome['entities']['location']:
          self.s['location'].append(loc['value'])

      # TODO: ideally each object in the state's datetime list should have a preference. What if the person says in the subsequent conversation, that
        # "Oh, actually 6p might work better, but if not I can happily meet at 4. ". An extended version of preference could also be dispreference -
        # changing his mind. for instance, "actually, I can only do 6p, sorry."
      if 'datetime' in outcome['entities']:
        for dt in outcome['entities']['datetime']:
          for dt_interpret in dt['values']:
            dtval = dateutil.parser.parse(dt_interpret['value'])
            wit_ai_bug = False
            for tmpdt in self.s['datetime']:
              tmpdtval = dateutil.parser.parse(tmpdt['value'])
              if dtval-tmpdtval > datetime.timedelta(days=365):
                wit_ai_bug = True
            if not wit_ai_bug:
              self.s['datetime'].append(dt_interpret)

            # in the following attempt, 'grain' information about datetime will be lost.
            # so we cannot distinguish betwn 'tomorrow' and 'tomorrow at 12am'
            # if dt_interpret['type'] == 'value':
            #   from_dt = dateutil.parser.parse(dt_interpret['value'])
            #   self.s['datetime'].append((from_dt, ))
            # elif dt_interpret['type'] == 'interval':
            #   from_dt = dateutil.parser.parse(dt_interpret['from']['value'])
            #   to_dt = dateutil.parser.parse(dt_interpret['from']['value'])
            #   self.s['datetime'].append((from_dt, to_dt))

      if 'duration' in outcome['entities']:
        for dur in outcome['entities']['duration']:
          self.s['duration'].append(dur)

    self.turns.append(info)
