import sendgrid
import datetime
import email
from email_reply_parser import EmailReplyParser
import os
import sys
import random
from planus.src.cal import *
from planus.src.ds import ds
from planus.src import google
import re
import base64
sys.path.append(os.path.abspath('/var/www/autos'))
from flask import request

SARA = 'sara@autoscientist.com'
SARA_F = 'Sara <sara@autoscientist.com>'
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

address_dict = {SARA: ['Sara', SARA_F]}

from pymongo import MongoClient
client = MongoClient() # get a client
db = client.sara.handles # get the database, like a table in sql
sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
gm = google.create_gmail_client()



def record_exists(thread_id):
    return (db.find_one({'thread_id':thread_id}) is not None)

def sara_get_body(msg):
    # sara_debug(msg.as_string())
    maintype = msg.get_content_maintype()
    # if maintype == 'multipart':
    if msg.is_multipart():
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    # elif maintype == 'text':
    else:
        return msg.get_payload()
    # else:
    #     sara_debug('EMAIL TYPE NOT SUPPORTED YET')
    #     return 'Sorry, Email type not supported. Content type =' + msg.get_content_maintype()

def sara_quote(msg):

    body = sara_get_body(msg)
    seq = [line for line in body.splitlines(True)]
    quoted_body = '> '.join(seq)
    date_tuple = email.utils.parsedate_tz(msg['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        time_body = local_date.strftime("On %a, %b %-d, %Y at %-H:%M %p,")
        time_body = time_body + " %s wrote:"%msg['From']
        return time_body + "\r\n\r\n> " + quoted_body
    else:
        return quoted_body

def random_body():
    return "Hi! This is Sara. Let's schedule a meeting at %d %s. \n Regards,\n Sara"%(random.randint(1,10), random.choice(['AM', 'PM']))

def sara_debug(string, eobj=None):
    if eobj is not None:
        logger.debug('[SARA]:: From:%s To:%s Subject:%s Body:%s::%s' %(eobj['from'],eobj['to'], eobj['subject'], EmailReplyParser.parse_reply(eobj.get_payload()), string))

    else:
        logger.debug('[SARA]::', string)

def sara_sanity(cc, sub):
    # sanity check to exclude type of communications we
    # dont want i.e., indirect mail, incorrect addr, Fwd's etc.
    if (cc is None) or (cc != SARA):
        sara_debug('[sanity]: CC field %s not correct'%cc)
        return "Fail"
    if len(sub) >= 4:
        if (sub.lower())[:4] == 'fwd:':
            sara_debug('[sanity]: Received a forwarding mail')
            return "Fail"
    return "Pass"


def strip_email(string):

    raw = []
    for item in string.split(','):
        m = re.search("\w+@\w+\.com", string.lower())
        each = m.group(0)
        address_dict[each] = [string[0:m.start()-2], item]
        raw.append(each)
    return raw

from pprint import pprint

def sara_handle(lastHistoryID):
    # pass the message handle to sara and take
    # appropriate action: if message_id doesn't
    # exist in database then create a new thread
    changes = google.ListHistory(gm, 'me', lastHistoryID)

    data = json.loads(base64.urlsafe_b64decode(request.json['message']['data'].encode("utf-8")))
    retHistoryID = data['historyId']
    pprint(changes)

    for history in changes:
        if 'messagesAdded' in history:
            for messages in history['messagesAdded']:

                message_id = messages['message']['id']
                message = google.GetMessage(gm, 'me', message_id)
                raw_email = base64.urlsafe_b64decode(message['raw'].encode("utf-8"))
                eobj = email.message_from_string(raw_email)

                header = eobj['headers']
                from_addr = strip_email(eobj['from']) # is a list
                to_addrs =  strip_email(eobj['to']) # is a list

                try:
                    sub = eobj['subject']
                except KeyError:
                    sara_debug('Subject missing', eobj)
                    sub = ''
                try:
                    body = eobj['text']
                except KeyError:
                    sara_debug('No body present', eobj)
                    body = ''
                try:
                    html = eobj['html']
                except KeyError:
                    sara_debug('No html body present', eobj)
                    html = ''
                try:
                    cc_addrs = strip_email(eobj['cc'])
                except KeyError:
                    sara_debug('CC missing', eobj)
                    cc_addrs = []

                # all to+cc addresses without sara
                to_plus_cc_addrs = [addr for addr in (to_addrs + cc_addrs) if addr != SARA]

                # ---------------------------------------------------------------------
                #                       RFC 2822
                # https://tools.ietf.org/html/rfc2822#section-3.6.4
                # ---------------------------------------------------------------------
                try:
                    references = eobj.get('References')
                except KeyError:
                    references = ''

                if references:
                    thread_id = references.split(' ')[0]
                else:
                    thread_id = eobj.get('Message-ID')

                if record_exists(thread_id):
                    sara_debug('Existing thread', eobj)
                    record = db.find_one({'thread_id': thread_id})
                    prev_elist = record['elist']
                    # anyone in the To/CC field apart from busy person
                    # and Sara is the free person
                    # TODO: Also remove other busy users who are also using Sara

                    fulist = record['fu']
                    bu = record['bu']
                    for addr in to_plus_cc_addrs:
                        if (addr not in fulist) and (addr != bu):
                            fulist.append(addr)

                else:
                    sara_debug('New thread', eobj)
                    # if sara_sanity(cc, sub) == 'Fail':
                    #    return "Do Nothing"

                    # who ever first sent a mail including Sara is the Busy person
                    bu = from_addr[0]
                    fulist = []
                    for addr in to_plus_cc_addrs:
                        fulist.append(addr)
                    prev_elist = []

                prev_elist.append(eobj.as_string())

                # update database
                res = db.update(
                    {'thread_id': thread_id},
                    {
                        'thread_id': thread_id,
                        'elist': prev_elist,
                        'bu': bu,
                        'fu': fulist,
                    },  upsert = True
                    )

                # do nothing for loopback messages
                if from_addr != SARA:
                    # receive(from_addr[0], to_plus_cc_addrs, eobj, thread_id, fulist, bu)

    return retHistoryID

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

    reply(to_addrs[0], cc_addrs, body, em, delete)
    # case where B -> S initially where within that email, he asks to setup
    # meeting with F, so S -> F is the current email, and you will have to
    # delete quote from B->S before sending S->F

    sara_debug("Finished sending")


def receive(from_addr, to_plus_cc_addrs, current_email, thread_id, fulist, bu):

    # the following if is simply to fix the state among all free users. If a new
    # free guy is added by the busy guy, please take the most recent state
    # among the free guys and add him to that. <-- this adding a free guy in the
    # middle has not been included in the below snippet within the if statement
    if from_addr in fulist:

        audience = [addr for addr in to_plus_cc_addrs if addr != bu]
        if audience and audience != fulist:
            adding_others_reply(fulist, current_email)
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
            'body': EmailReplyParser.parse_reply(sara_get_body(current_email)),
          },

    'availability': {
                  'dt': get_free_slots(bu), # list of tuples of dt objects
                  'loc': "Starbucks",
                }
            }


    dsobj = ds(thread_id[1:-1]) # if tid is None ds will pass a brand new object
    output_obj = dsobj.take_turn(input_obj)


    for each_email in output_obj['emails']:
        to_addrs = list(each_email['to'])
        sara_debug("INPUTTTTTTTT"+','.join(to_addrs))
        to_addrs = [address_dict[item][1] for item in to_addrs]
        body = each_email['body']
        send(to_addrs, body, thread_id)

    if output_obj['meeting'] is not None:
        send_invite(bu, fulist, output_obj['meeting']['loc'], output_obj['meeting']['dt']['start'], output_obj['meeting']['dt']['end'])


    sara_debug("Finished receiving")


def adding_others_reply(fulist, last_email):

    msg = sendgrid.Mail()
    msg.add_to(last_email['from'])
    msg.add_cc( ",".join([SARA_F] + [addr for addr in fulist if addr != last_email['from']]))
    msg.set_subject(last_email['subject'])
    msg.set_text("Adding Others" + "\r\n\r\n> " + sara_quote(last_email))
    msg.set_from(SARA_F)
    msg.set_headers({"In-Reply-To": last_email["Message-ID"], "References": last_email['References'] + " " +last_email["Message-ID"]})
    status, msg = sg.send(msg)

from email.mime.text import MIMEText

def reply(to_addrs, cc_addrs, new_body, last_email, delete):

    if delete:
        msg.MIMEText(new_body)
    else:
        msg = MIMEText(new_body + "\r\n\r\n> " + sara_quote(last_email))

    msg['to'] = to_addrs
    sara_debug("SARA CCCCCC"+SARA_F + ("," + cc_addrs if cc_addrs else ""))

    msg['cc'] = SARA_F + ("," + cc_addrs if cc_addrs else "")
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

    if last_email['References']:
        msg.add_header({"In-Reply-To": last_email["Message-ID"], "References": last_email['References'] + " " +last_email["Message-ID"]})
    else:
        msg.add_header({"In-Reply-To": last_email["Message-ID"], "References": last_email["Message-ID"]})

    message = {'raw': base64.b64encode(msg.as_string())}
    google.SendMessage(gm, 'me', message)