import sendgrid
import datetime
import email
from email_reply_parser import EmailReplyParser
import os
import sys
import random
# from src.ds import ds

sys.path.append(os.path.abspath('/var/www/autos'))
from autoviz import *

SARA = 'sara@autoscientist.com'
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
sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')


def record_exists(sara_id):
    return (db.find_one({'sara_id':sara_id}) is not None)

def sara_get_body(msg):
    maintype = msg.get_content_maintype()
    if maintype == 'multipart':
        for part in msg.get_payload():
            if part.get_content_maintype() == 'text':
                return part.get_payload()
    elif maintype == 'text':
        return msg.get_payload()

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

def sara_debug(string):
    logger.debug('[SARA]:: From:%s To:%s Subject:%s Body:%s::%s' %(request.form['from'],request.form['to'], request.form['subject'], EmailReplyParser.parse_reply(request.form['text']), string))

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


def sara_handle():
    # pass the message handle to sara and take
    # appropriate action: if message_id doesn't
    # exist in database then create a new thread

    sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
    header = request.form['headers']
    from_addr = request.form['from']
    to_addr =  request.form['to']

    try:
        sub = request.form['subject']
    except KeyError:
        sara_debug('Subject missing')
        sub = ''
    try:
        body = request.form['text']
    except KeyError:
        sara_debug('No body present')
        body = ''
    try:
        html = request.form['html']
    except KeyError:
        sara_debug('No html body present')
        html = ''
    try:
        cc_addrs = request.form['cc']
    except KeyError:
        sara_debug('CC missing')
        cc_addrs = ''

    # all to+cc addresses without sara
    to_plus_cc_addrs = [addr for addr in (to_addrs + "," + cc_addrs).split(',') if addr != SARA]

    raw_email = header + "\r\n\r\n" + body
    eobj = email.message_from_string(raw_email)

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
        sara_debug('Existing thread')
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
        sara_debug('New thread')
        # if sara_sanity(cc, sub) == 'Fail':
        #    return "Do Nothing"

        # who ever first sent a mail including Sara is the Busy person
        bu = from_addr
        fulist = []
        for addr in to_plus_cc_addrs:
            fulist.append(addr)
        prev_elist = []

    new_elist = prev_elist.append(eobj.as_string())

    # update database
    res = db.update(
        {'thread_id': thread_id},
        {
            'thread_id': thread_id,
            'elist': new_elist,
            'bu': bu,
            'fu': fulist,
        },  upsert = True
        )

    # do nothing for loopback messages
    if from_addr != SARA:
        receive(from_addr, to_plus_cc_addrs, eobj, thread_id)

    return "Ok"

def find_last_involvement(to_addrs, thread_id):
    record = db.find_one({'thread_id': thread_id})
    elist = record['elist']
    for item in reversed(elist):
        em = email.message_from_string(item)
        all_addrs = em['To'] + "," + em['From'] + (","+ em['CC'] if em['CC'] else '')
        if to_addrs <= set(all_addrs):
            return em

def send(to_addrs, body, thread_id):
    # to_addrs      :   list of addresses
    em = find_last_involvement(to_addrs, thread_id);
    if len(to_addrs) > 1:
        to_addrs = to_addrs[0]
        cc_addrs = ",".join(to_addrs[1:])
    else:
        cc_addrs = ''

    if not em:
        reply(to_addrs, cc_addrs, body, em, delete=False)
    else:
        reply(to_addrs, cc_addrs, body, em, delete=True)
        # case where B -> S initially where within that email, he asks to setup
        # meeting with F, so S -> F is the current email, and you will have to
        # delete quote from B->S before sending S->F

    sara_debug("Finished sending")


def receive(from_addr, to_plus_cc_addrs, current_email, thread_id):

    # the following if is simply to fix the state among all free users. If a new
    # free guy is added by the busy guy, please take the most recent state
    # among the free guys and add him to that. <-- this adding a free guy in the
    # middle has not been included in the below snippet within the if statement
    if from_addr in fulist:

        audience = [addr for addr in to_plus_cc_addrs if addr != bu]
        if audience and audience != fulist:
            adding_others_reply(fulist, current_email)
            to_plus_cc_addrs = fulist

    input_obj = {
    'email': {
            # 'from': ('last_name', 'first_name'),
            'from': re.search("\w+@\w+\.com", from_addr).group(0),
            'to': re.search("\w+@\w+\.com", to_plus_cc_addrs + [SARA]).group(0),
            'body': EmailReplyParser.parse_reply(sara_get_body(current_email)),
          },

    'availability': {
                  'avail_datetime': [], # list of tuples of datetime objects
                  'avail_location': None, # some form of object, decide when we know more later
                }
            }

    dsobj = ds(thread_id) # if tid is None ds will pass a brand new object
    dsobj.take_turn(input_obj)
    sara_debug("Finished receiving")


def adding_others_reply(fulist, last_email):

    msg = sendgrid.Mail()
    msg.add_to(last_email['from'])
    msg.add_cc( ",".join([SARA] + [addr for addr in fulist if addr != last_email['from']]))
    msg.set_subject(last_email['subject'])
    msg.set_text("Adding Others" + "\r\n\r\n> " + sara_quote(last_email))
    msg.set_from(SARA)
    msg.set_headers({"In-Reply-To": last_email["Message-ID"], "References": last_email['References'] + " " +last_email["Message-ID"]})
    status, msg = sg.send(msg)


def reply(to_addrs, cc_addrs, new_body, last_email, delete):

    msg = sendgrid.Mail()
    msg.add_to(to_addrs)
    msg.add_cc(SARA + ("," + cc_addrs if cc_addrs else ""))

    sub = last_email['subject']
    if len(sub) < 3:
        new_sub = 'Re:'+sub
    else:
        if (sub.lower()[0:3] == 're:'):
           new_sub = sub
        else:
            new_sub = 'Re:'+sub
    msg.set_subject(new_sub)

    if delete:
        msg.set_text(new_body)
    else:
        msg.set_text(new_body + "\r\n\r\n> " + sara_quote(last_email))

    msg.set_from(SARA)
    msg.set_headers({"In-Reply-To": last_email["Message-ID"]})
    if last_email['References']:
        msg.set_headers({"References": last_email['References'] + " " +last_email["Message-ID"]})
    else:
        msg.set_headers({"References": last_email["Message-ID"]})

    status, msg = sg.send(msg)

