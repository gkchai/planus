import datetime
import email
from email_reply_parser import EmailReplyParser
import os
import sys
import random
import re
import base64
from email.mime.text import MIMEText
from pprint import pprint

# local code
from planus.src.cal import *
from planus.src.ds import ds
from planus.src import google
from planus.util import mail
from planus.util.mail import address_dict, SARA, SARA_F


LOG_DIR = '/var/www/autos/planus/log/'

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
# handler = logging.FileHandler(LOG_DIR+'runtime.log')
# handler.setLevel(logging.INFO)

# create a logging format
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)

# add the handlers to the logger
# logger.addHandler(handler)


from pymongo import MongoClient
client = MongoClient() # get a client
db = client.sara.handles # get the database, like a table in sql
gm = google.create_gmail_client()


def record_exists(thread_id, message_id=None):
    if message_id is not None:
        return (db.find_one({'message_id':message_id}) is not None)
    else:
        return (db.find_one({'thread_id':thread_id}) is not None)



def sara_debug(string, eobj=None):
    if eobj is not None:
        body = mail.get_body(eobj)
        if body is not None:
            logger.debug('[SARA]:: From:%s To:%s Subject:%s Body:%s::%s' %(eobj['from'],eobj['to'], eobj['subject'], EmailReplyParser.parse_reply(body), string))
        else:
            logger.debug('[SARA]:: From:%s To:%s Subject:%s ::%s' %(eobj['from'],eobj['to'], eobj['subject'], string))
    else:
        logger.debug('[SARA]::%s'%(string))





def sara_handle(message_id, thread_id):

    sara_debug('[HANDLE]: message_id=%s, thread_id=%s'%(message_id, thread_id))
    message = google.GetMessage(gm, 'me', message_id)
    raw_email = base64.urlsafe_b64decode(message['raw'].encode("utf-8"))
    eobj = email.message_from_string(raw_email)

    header = eobj['headers']
    from_addr = mail.strip(eobj['from']) # is a list
    to_addrs =  mail.strip(eobj['to']) # is a list

    sub = eobj['subject']
    if sub is None or sub == '':
        sara_debug('Subject missing', eobj)

    if mail.get_body(eobj) is None:
        sara_debug('No body present', eobj)

    if eobj['cc'] is None or eobj['cc'] == '':
        sara_debug('No CC')
        cc_addrs = []
    else:
        cc_addrs = mail.strip(eobj['cc'])

    # all to+cc addresses without sara
    to_plus_cc_addrs = [addr for addr in (to_addrs + cc_addrs) if addr != SARA]

    # ---------------------------------------------------------------------
    #                       RFC 2822
    # https://tools.ietf.org/html/rfc2822#section-3.6.4
    # ---------------------------------------------------------------------

    references = eobj['References']
    if references is not None:
        raw_id = references.split(' ')[0]
    else:
        raw_id = eobj.get('Message-ID')

    prev_elist, prev_mlist = [], []
    record = db.find_one({'thread_id': thread_id})

    if record is not None:
        sara_debug('Existing thread', eobj)
        prev_elist = record['elist']
        prev_mlist = record['mlist']
        # anyone in the To/CC field apart from busy person
        # and Sara is the free person
        # TODO: Also remove other busy users who are also using Sara

        # dont update if we recieve the same message
        # will happen when a history push notification was not
        # acknowledged
        if message_id not in record['mlist']:
            prev_elist.append(eobj.as_string())
            prev_mlist.append(message_id)
        else:
            sara_debug('Existing message', eobj)
            # return

        fulist = record['fu']
        bu = record['bu']
        for addr in to_plus_cc_addrs:
            if (addr not in fulist) and (addr != bu):
                fulist.append(addr)

    else:
        sara_debug('New thread/message', eobj)

        # who ever first sent a mail including Sara is the Busy person
        bu = from_addr[0]
        fulist = []
        for addr in to_plus_cc_addrs:
            fulist.append(addr)

        prev_elist.append(eobj.as_string())
        prev_mlist.append(message_id)


    # update database
    res = db.update(
        {'thread_id': thread_id},
        {
            'thread_id': thread_id,
            'elist': prev_elist,
            'mlist': prev_mlist,
            'bu': bu,
            'fu': fulist,
        },  upsert = True
        )

    # do nothing for loopback messages
    if from_addr[0] != SARA:
        receive(from_addr[0], to_plus_cc_addrs, eobj, thread_id, fulist, bu)
    else:
        sara_debug('BCC message', eobj)



def find_last_involvement(to_addrs, thread_id):
    record = db.find_one({'thread_id': thread_id})
    elist = record['elist']

    # sara_debug(elist[0])
    for item in reversed(elist):
        em = email.message_from_string(item)
        all_addrs = (em['To'].split(',')) +  [em['From']] + (em['CC'].split(',') if em['CC'] else [])

        sara_debug('HERRRRRR'+','.join(to_addrs))
        if set(to_addrs) <= set(all_addrs):
            return em, False

    # no involvement found, so delete quoted text
    return email.message_from_string(elist[-1]), True


def send(to_addrs, body, thread_id):
    # to_addrs      :   list of addresses
    sara_debug('HERRRRRR'+','.join(to_addrs))
    em, delete = find_last_involvement(to_addrs, thread_id);

    if len(to_addrs) > 1:
        cc_addrs = ",".join(to_addrs[1:])
    else:
        cc_addrs = ''

    result = reply(to_addrs[0], cc_addrs, body, em, delete, thread_id)
    # case where B -> S initially where within that email, he asks to setup
    # meeting with F, so S -> F is the current email, and you will have to
    # delete quote from B->S before sending S->F
    sara_debug("Finished sending")
    return result

def receive(from_addr, to_plus_cc_addrs, current_email, thread_id, fulist, bu):

    try:
        # the following is simply to fix the state among all free users. If a new
        # free guy is added by the busy guy, please take the most recent state
        # among the free guys and add him to that. <-- this adding a free guy in the
        # middle has not been included in the below snippet within the if statement
        if from_addr in fulist:

            audience = [addr for addr in to_plus_cc_addrs if addr != bu]
            if audience and audience != fulist:
                adding_others_reply(fulist, current_email, thread_id)
                to_plus_cc_addrs = fulist

        person_list = []
        for item in to_plus_cc_addrs:

            person_list.append({
                    'email': item,
                    'first_name': address_dict[item][0]
                    }
                )

        from_entry = {
                        'email': from_addr,
                        'first_name': address_dict[from_addr][0]
                    }

        input_obj = {
        'email': {
                'from': from_entry,
                'to': person_list,
                'body': EmailReplyParser.parse_reply(mail.get_body(current_email)),
              },

        'availability': {
                      'dt': get_free_slots(bu), # list of tuples of dt objects
                      'loc': "Starbucks",
                    }
                }

        sara_debug('INPUTTT'+input_obj.__str__())
        dsobj = ds(thread_id) # if tid is None ds will pass a brand new object

        output_obj = dsobj.take_turn(input_obj)
        sara_debug('OUTPUTTT '+output_obj.__str__())

        for each_email in output_obj['emails']:
            to_addrs = list(each_email['to'])
            sara_debug("INPUTTTTTTTT"+','.join(to_addrs))
            to_addrs = [address_dict[item][1] for item in to_addrs]
            body = each_email['body']
            send(to_addrs, body, thread_id)

        if output_obj['meeting'] is not None:
            send_invite(SARA_F, list(output_obj['meeting']['to']), output_obj['meeting']['loc'], output_obj['meeting']['dt']['start'], output_obj['meeting']['dt']['end'])

        sara_debug("Finished receiving...Returning")
        return 'success'

    except Exception as e:

        print e
        print sys.exc_info()[0]
        sara_debug("Failed receiving...Returning")
        return 'Failure'

def adding_others_reply(fulist, last_email, thread_id):

    msg = MIMEText(new_body)
    msg = MIMEText("Adding Others" + "\r\n\r\n> " + mail.quote(last_email))
    msg['cc'] = ( ",".join([SARA_F] + [addr for addr in fulist if addr != last_email['from']]))
    msg['subject'] = last_email['subject']
    msg['from'] = SARA_F
    msg.add_header("In-Reply-To", last_email["Message-ID"])
    msg.add_header("References", last_email['References'] + " " +last_email["Message-ID"])
    message = {'threadId': thread_id, 'raw': base64.urlsafe_b64encode(msg.as_string())}
    result = google.SendMessage(gm, 'me', message, thread_id)
    if result is not None:
        return 'success'


def reply(to_addrs, cc_addrs, new_body, last_email, delete, thread_id):

    if delete:
        msg = MIMEText(new_body)
    else:
        msg = MIMEText(new_body + "\r\n\r\n> " + mail.quote(last_email))

    msg['to'] = to_addrs
    if cc_addrs is not None:
        msg['cc'] = cc_addrs

    msg['bcc'] = SARA_F
    sara_debug("SARA CCCCCC"+SARA_F + ("," + cc_addrs if cc_addrs else ""))

    sub = last_email['subject']
    if len(sub) < 3:
        new_sub = 'Re:'+sub
    else:
        if (sub.lower()[0:3] == 're:'):
           new_sub = sub
        else:
            new_sub = 'Re:'+sub
    msg['subject'] = new_sub
    msg['from'] = SARA_F

    msg.add_header("In-Reply-To", last_email["Message-ID"])

    if last_email['References'] is not None:
        msg.add_header("References", last_email['References'] + " " +last_email["Message-ID"])
    else:
        msg.add_header("References", last_email["Message-ID"])


    message = {'threadId': thread_id, 'raw': base64.urlsafe_b64encode(msg.as_string())}
    result = google.SendMessage(gm, 'me', message, thread_id)

    if result is not None:
        return 'success'