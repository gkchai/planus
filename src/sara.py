import sendgrid
import datetime
import email
from email_reply_parser import EmailReplyParser
import os
import sys
import cPickle as pickle
import random

sys.path.append(os.path.abspath('/var/www/autos'))
from autoviz import *

SARA_NAME = 'sara@autoscientist.com'
LOG_DIR = '/var/www/autos/planus/log/'

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create a file handler
handler = logging.FileHandler(LOG_DIR+'runtime.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)

from pymongo import MongoClient
client = MongoClient() # get a client
db = client.sara.handles # get the database, like a table in sql


def write_log(filename, data, opt='a'):
    with open(filename, opt) as fo:
        fo.write(data)

def write_pickle(filename, data):
    with open(filename, 'wb') as fo:
        pickle.dumps(data)
        pickle.dump(data, fo,  protocol=pickle.HIGHEST_PROTOCOL)


def read_pickle(filename):
    if os.path.exists(filename):
        with open(filename ,'rb') as fo:
            data = pickle.load(fo)
    else:
        data = {}
    return data

def record_exists(sara_id):
    return (db.find_one({'sara_id':sara_id}) is not None)


def sara_quote(text):
    # quote given text with '>'
    seq = [line for line in text.splitlines(True)]
    return '>'.join(seq)

def sara_parseheader(header):
    hparser = email.Parser.HeaderParser()
    hd = hparser.parsestr(header)
    return hd

def sara_debug(string):
    logger.debug('[SARA]: From:%s To:%s Subject:%s Body:%s::%s' %(request.form['from'],request.form['to'], request.form['subject'], EmailReplyParser.parse_reply(request.form['text']), string))

def sara_sanity(cc, sub):
    # sanity check to exclude type of communications we
    # dont want i.e., indirect mail, incorrect addr, Fwd's etc.

    if (cc is None) or (cc != SARA_NAME):
        sara_debug('[sanity]: CC field not correct')
        return "Fail"

    if len(sub) >= 4:
        if (sub.lower())[:4] == 'fwd:':
            sara_debug('[sanity]: Received a forwarding mail')
            return "Fail"

    return "Pass"


def sara_handle():
    # pass the message handle to sara and take
    # appropriate action: if email_id doesn't exist then
    # create new instance else do a state transition

    # dictionary of email_ids and class instances
    sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
    header = request.form['headers']
    who = request.form['from']
    to =  request.form['to']

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
        cc = request.form['cc']
    except KeyError:
        sara_debug('CC missing')
        cc = ''


    hd = sara_parseheader(header)

    # ---------------------------------------------------------------------
    #                       RFC 2822
    # https://tools.ietf.org/html/rfc2822#section-3.6.4
    # ---------------------------------------------------------------------
    # The "In-Reply-To:" and "References:" fields are used when creating a
    # reply to a message.  They hold the message identifier of the original
    # message and the message identifiers of other messages (for example,
    # in the case of a reply to a message which was itself a reply).  The
    # "In-Reply-To:" field may be used to identify the message (or messages)
    # to which the new message is a reply, while the "References:" field may
    # be used to identify a "thread" of conversation.
    # ----------------------------------------------------------------------

    try:
        references = hd.get('References')
    except KeyError:
        references = ''

    if references:
        sara_id = references.split(' ')[0]
    else:
        sara_id = hd.get('Message-ID')

    ####################################
    # Two possible starts of interaction
    # First:
        # k)   Busy <====> Free
        # k+1) Busy ====> Free (CC: Sara)
    # Second:
        # 1) Busy ====> Free (CC: Sara)
    #####################################

    if hd.has_key('In-Reply-To'):
        start = 'Any'
    else:
        start = 'Busy'


    if record_exists(sara_id):

        sara_debug('Existing thread')
        record = db.find_one({'sara_id': sara_id})
        bu = record['bu']
        fu = record['fu']
        sara_obj = sara(bu, fu, sub, body, html, hd, start, sara_id)
        sara_obj.speak("Hi. This is Sara%d"%random.randint(1,100), 1)

    else:

        sara_debug('New thread')
        if sara_sanity(cc, sub) == 'Fail':
           return "Do Nothing"
        else:
            bu = who
            fu = to
            sara_obj = sara(bu, fu, sub, body, html, hd, start, sara_id)
            sara_obj.speak("Hi. This is Sara%d"%random.randint(1,100), 0)
    # end if

    sara_obj.listen()
    # update database
    res = db.update(
        {'sara_id': sara_id},
        {
            'sara_id': sara_id,
            "bu": bu,
            "fu": fu,
            "sub": sub,
            "body": body,
            "html": html,
            "hd": hd.as_string(),
            "start": start
        },  upsert = True
        )

    # sara_debug("Finished speaking: nMatched=%d, nUpserted=%d, nModified=%d"%(res['nMatched'], res['nUpserted'], n['nModified']))
    sara_debug("Finished speaking")
    return "Ok"



class sara():
    # class for our personal assistant Sara's interaction

    def __init__(self, busy_user, free_user, sub, body, html, hd, start, s_id):
        self.bu = busy_user
        self.fu = free_user
        self.sub = sub
        self.start = start
        self.id = s_id
        self.creation_date = datetime.datetime.now()
        self.last_body = body
        self.last_html = html
        self.last_header = hd


    def speak(self, string, count):
        # send email to free user with the given string

        sara_debug("start speaking")
        new_body = string

        if len(self.sub) < 3:
            new_sub = 'Re:'+self.sub
        else:
            if (self.sub.lower()[0:3] == 're:'):
                new_sub = self.sub
            else:
                new_sub = 'Re:'+self.sub

        if self.start == 'Busy' and count == 0:
            # In this case, busy user initiated mail and CCed
            # to Sara. Sara replies on top of that mail to the
            # free user

            new_in_reply_to = self.last_header.get('Message-ID')
            new_references = new_in_reply_to
        else:
            # Regular case where Sara replies on top of the
            # previous mail (from free user or the busy user)

            new_in_reply_to = self.last_header.get('Message-ID')
            new_references = self.last_header.get('References') + " " + new_in_reply_to


        msg = sendgrid.Mail()
        msg.add_to(self.fu)
        msg.set_subject(new_sub)
        msg.set_text(new_body + "\n\n>" + sara_quote(self.last_body))
        msg.set_from(SARA_NAME)
        msg.set_headers({"In-Reply-To": new_in_reply_to, "References": new_references})

        sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
        status, msg = sg.send(msg)


        return status

    def listen(self):
        # listen to free
        # extract the new text

        new_text = EmailReplyParser.parse_reply(self.last_body)

