#!/usr/bin/python
# -*- coding: utf-8 -*-

# Dialog system using state machine. State machine for sara seems to be simple.
# States  = {init, scheduling, scheduled, trap}
# Inputs = {datetime mail, confirm mail, trap mail}
# Outputs = {do nothing, signup mail, probe mail, invite mail}
# Transitions = {...}
#
# It is the latent variables and the corresponding rules for outputs that are
# non-trivial.
# Latent variables are datetime summary states,  no. of people asked, no. of people
# responded etc.
# Output rules must handle diverse cases: Free slots can change midway, an update
# mail can be sent after 'scheduled', update mail can occur on top of previous
# update mail, people can be added during 'scheduling' etc.
#
# A good design makes it easy to add/update rules. Initially, special cases will
# be pushed to 'trap' (for human to resolve). Over time, rules will be written
# to handle these cases.

from planus.src.nlu import nlu
import datetime, dateutil.parser

from pymongo import MongoClient
client = MongoClient()
db = client.sara.gds

# greeting string
def greeting(num_users, name_list):
    if name_list == []:
        if num_users <= 1:
            return 'Hello,'
        else:
            return 'Dear All,'
    else:
        assert(num_users == len(name_list))
        if num_users == 1:
            return 'Hi %s,'%(name_list[0])
        elif num_users == 2:
            return 'Hi %s and %s,'%(name_list[0], name_list[1])
        else:
            return 'Dear All,'


def expand_dt(dt):
    return dt.strftime('%a %d %b %I:%M%p')

def find_common_dt(dt_request, dt_avail):
    pass



# class with latent variables
class gdm:
    def __init__(self):
        pass

    def load_var(self, latent_var):
        self.dlg_id = latent_var['dlg_id']
        self.b_ids = latent_var['b_ids']
        self.f_ids = latent_var['f_ids']
        self.b_names = latent_var['b_names']
        self.f_names = latent_var['f_names']
        self.obj_inputs = latent_var['obj_inputs']
        self.curr_state_str = latent_var['curr_state_str']
        self.avail_dts = latent_var['avail_dts']
        self.seq_in = latent_var['seq_in']
        self.seq_out = latent_var['seq_out']
        self.loc = latent_var['loc']
        self.dlg_count = latent_var['dlg_count']



    def act_info(self, input):

        if self.dlg_count == 0:
            self.b_ids.append(input['email']['from']['email'])
            self.b_names.append(input['email']['from']['first_name'])
            for person in input['email']['to']:
                self.f_ids.append(person['email'])
                if not person['first_name'] == None:
                    self.f_names.append(person['first_name'])
            self.dlg_count += 1



    def act_in(self, nlu, input):
        in_text = input['email']['body']
        out_nlu = nlu.get_dialog_act(in_text)
        obj_act_in = {'type': 'trap', 'values': []}

        try:
            outcome = out_nlu['outcomes'][0]
            if outcome['confidence'] > 0.5:
                if outcome['entities'].has_key('datetime'):
                    obj_act_in['type'] = 'datetime'

                    for dt_item in outcome['entities']['datetime'][0]['values']:
                        obj_act_in['values'].append( dateutil.parser.parse(dt_item['value']))

                    if outcome['entities'].has_key('location'):
                        self.loc.append(outcome['entities']['location'][0]['value'])
                elif outcome['intent'] == 'suggestion':
                    obj_act_in['type'] = 'confirm'

        except KeyError:
            print 'Wit.ai error'

        return obj_act_in


    def act_out(self, obj_act_out):

        if obj_act_out == None:
            return None

        obj_out = {'meeting': None,'emails': []}

        if obj_act_out['type'] == 'signup':
            assert(len(self.b_ids) == 1)
            obj_out['emails'] = [
                          {
                            'to': set(self.b_ids), # set of email ids, first is to and rest is cc during sending this email,
                            'body': '%s \n\nI cannot connect to your calendar. Please signup with your google account at\nhttps://autoscientist.com/login?key=%s&email=%s to use this service.\n\nRegards,\n\nSara'%(greeting(1, self.b_names), self.dlg_id, self.b_ids[0])
                          },
                        ]

        if obj_act_out['type'] == 'probe':
            obj_out['emails'] = [
                          {
                            'to': set(obj_act_out['tos']), # set of email ids, first is to and rest is cc during sending this email,
                            'body': '%s \n\nWill %s work for you ? \n\nRegards,\n\nSara'%(greeting( len(obj_act_out['names']), obj_act_out['names']), expand_dt(obj_act_out['datetime']))
                          },
                        ]


        if obj_act_out['type'] == 'invite':

            obj_out['meeting'] = {
                            'to': set(self.b_ids + self.f_ids) ,
                            'loc': self.loc[0] if not self.loc == [] else 'Location',
                            'dt':{'start': obj_act_out['datetime'],
                                 'end': obj_act_out['datetime'] + datetime.timedelta(minutes=30)}

            }

            obj_out['emails'] = [
                          {
                            'to': set(obj_act_out['tos']), # set of email ids, first is to and rest is cc during sending this email,
                            'body': '%s \n\nThank you for helping me schedule your meeting. You will shortly receive a calendar invite for the meeting set up at %s.\n\nYou are all set, have a great day! If you would like to reschedule at anytime, you can reply me back. \n\nRegards,\n\nSara'%(greeting( len(obj_act_out['names']), obj_act_out['names']), expand_dt(obj_act_out['datetime']))
                          },
                        ]


        return obj_out



    def do_take_turn(self, input):
        self.obj_inputs.append(input)
        str_state_dict = {'init':s_init, 'scheduling':s_scheduling, 'scheduled':s_scheduled, 'trap':s_trap}
        str_state_dict[self.curr_state_str].action()
        obj_act_out, self.curr_state_str = str_state_dict[self.curr_state_str].next(self, input)
        return obj_act_out



# state placeholder
class state:
    def __init__(self):
        self.obj_act_out = {'type': None, 'tos': [], 'names':[], 'datetime': None}

    def action(self):
        raise NotImplementedError
    def next(self, input):
        raise NotImplementedError



# Define states
class init(state):
    def action(self):
        pass

    def next(self, obj_gdm, obj_act_in):
        if obj_gdm.avail_dts == None:
            self.obj_act_out['type'] = 'signup'
            return self.obj_act_out, 'init'

        if obj_act_in['type'] == 'datetime':

            # haven't asked anyone yet so go ahead probe
            self.obj_act_out['type'] = 'probe'
            self.obj_act_out['tos'] = obj_gdm.f_ids
            self.obj_act_out['names'] = obj_gdm.f_names
            self.obj_act_out['datetime'] = obj_act_in['values'][0]
            return self.obj_act_out, 'scheduling'

        if obj_act_in['type'] == 'trap':
            return None, 'trap'


# Define states
class scheduling(state):
    def action(self):
        pass

    def next(self, obj_gdm, obj_act_in):
        if obj_act_in['type'] == 'datetime':

            # confirm on the mentioned datetime
            # TODO: match the datetimes
            self.obj_act_out['type'] = 'invite'
            self.obj_act_out['tos'] = obj_gdm.f_ids
            self.obj_act_out['names'] = obj_gdm.f_names
            self.obj_act_out['datetime'] = obj_act_in['values'][0]
            return self.obj_act_out, 'scheduled'

        if obj_act_in['type'] == 'confirm':
            # TODO: fix this
            return None, 'scheduled'

        if obj_act_in['type'] == 'trap':
            return None, 'trap'


# Define states
class scheduled(state):
    def action(self):
        pass
    def next(self, obj_gdm, obj_act_in):
        return None, 'trap'


# Define states
class trap(state):
    def action(self):
        print 'Entered **TRAP**'

    def next(self, obj_gdm, obj_act_in):
        return None, 'trap'



# global static variables
s_init = init()
s_scheduling = scheduling()
s_scheduled = scheduled()
s_trap = trap()


# dialogue system
class gds:
    def __init__(self, dlg_id):
        self.dlg_nlu = nlu()
        self.dlg_id = dlg_id
        self.dlg_mngr = gdm()

    # parses the body of input object, fetches free slots of busy user,
    # moves the state machine and return the output object
    def take_turn(self, obj_in):

        rec = db.find_one({'dlg_id': self.dlg_id})
        if rec is not None:
            # old dialog, recover state
            print 'Existing record'
            latent_var = rec['var']
        else:
            # new dialog, initialize states
            print 'New record'
            latent_var = {
                            'dlg_id': self.dlg_id,
                            'b_ids' : [],
                            'f_ids' : [],
                            'b_names' : [],
                            'f_names' : [],
                            'obj_inputs' : [],
                            'curr_state_str' : 'init',
                            'avail_dts' : [],
                            'seq_in' : [],
                            'seq_out' : [],
                            'loc' : [],
                            'dlg_count' : 0,
                        }

        self.dlg_mngr.load_var(latent_var)

        print 'Taking turn'
        self.dlg_mngr.act_info(obj_in)
        print 'Done info'
        self.obj_act_in = self.dlg_mngr.act_in(self.dlg_nlu, obj_in)
        print 'Done act in', self.obj_act_in
        self.dlg_mngr.avail_dts = obj_in['availability']['dt']
        print 'Avail DTS', self.dlg_mngr.avail_dts
        out = self.dlg_mngr.do_take_turn(self.obj_act_in)
        print 'Out', out

        latent_var = {}
        latent_var['dlg_id']  = self.dlg_mngr.dlg_id
        latent_var['b_ids']  = self.dlg_mngr.b_ids
        latent_var['f_ids'] = self.dlg_mngr.f_ids
        latent_var['b_names'] = self.dlg_mngr.b_names
        latent_var['f_names'] = self.dlg_mngr.f_names
        latent_var['obj_inputs'] = self.dlg_mngr.obj_inputs
        latent_var['curr_state_str'] = self.dlg_mngr.curr_state_str
        latent_var['avail_dts'] = self.dlg_mngr.avail_dts
        latent_var['seq_in'] = self.dlg_mngr.seq_in
        latent_var['seq_out'] = self.dlg_mngr.seq_out
        latent_var['loc'] = self.dlg_mngr.loc
        latent_var['dlg_count'] = self.dlg_mngr.dlg_count

        # save to database
        db.update({'dlg_id': self.dlg_id}, {'dlg_id': self.dlg_id, 'var' : latent_var}, upsert=True)



        obj_out = self.dlg_mngr.act_out(out)
        return obj_out