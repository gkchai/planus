import sendgrid
import datetime
import email
from email_reply_parser import EmailReplyParser
import os
import sys

sys.path.append(os.path.abspath('/var/www/autos'))
from autoviz import *

SARA_NAME = 'sara@autoscientist.com'

# dictionary of email_ids and class instances
# {msg_id: sara_object}
sara_dict = {}

def write_pickle(data):
    import cPickle as pickle
    # pickle.dump(data, open('/var/www/autos/planus/log/sara.log' ,'a'))
    open('/var/www/autos/planus/log/sara.log' ,'a').write(data)


def sara_parseheader(header):
    hparser = email.Parser.HeaderParser()
    hd = hparser.parsestr(header)
    return hd

def sara_debug(string):
    # app.logger.debug('[SARA:] From:%s To:%s Subject: %s', (request.form['from'],
    write_pickle('[SARA]: From:%s To:%s Subject: %s' %(request.form['from'],
    request.form['to'], request.form['subject']))
    # app.logger.debug('[SARA:]'+string)
    write_pickle('[SARA]:'+string)


def sara_ifexists(id):
    # given an email_id check if that object already exists
    return (id in sara_dict)

def sara_sanity(cc, sub):
    # sanity check to exclude type of communications we
    # dont want i.e., indirect mail, incorrect addr, Fwd's etc.

    if (cc is None) or (cc != SARA_NAME):
        sara_debug('CC field not correct')
        return "Fail"

    if len(sub) >= 4:
        if (sub.lower())[:4] == 'fwd:':
            sara_debug('Received a forwarding mail')
            return "Fail"

    return "Pass"


def sara_handle():
    # pass the message handle to sara and take
    # appropriate action: if email_id doesn't exist then
    # create new isntance else do a state transition

    sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
    header = request.form['headers']
    who = request.form['from']
    to =  request.form['to']

    try:
        sub = request.form['subject']
    except KeyError:
        sara_debug('No subject present')
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
        sara_debug('No cc present')
        cc = ''


    if sara_sanity(cc, sub) == 'Fail':
        return "Do Nothing"
    else:

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


        if sara_ifexists(sara_id):
            sara_debug('Response belongs to existing thread')
            sara_obj = sara_dict[sara_id]

        else:
            sara_debug('New thread started')

            ####################################
            # Two possible starts of interaction
            # First:
                # 1) Busy <==== Free
                # 2) Busy ====> Free (CC: Sara)
            # Second:
                # 1) Busy ====> Free (CC: Sara)
            #####################################

            if hd.has_key('In-Reply-To'):
                bu = who
                fu = to
                start = 'Free'
            else:
                bu = to
                fu = who
                start = 'Busy'

            sara_obj = sara(bu, fu, sub, body, html, hd, start, sara_id)
            sara_dict[sara_id] = sara_obj

        # end if

        sara_obj.add_request()
        sara_obj.listen()
        sara_obj.speak("Hi. This is Sara. I will convince you that I am human.")
        sara_debug("Finished speaking"+ sara_obj.id)
        return "Ok"


class sara():
    # class for our personal assistant Sara
    def __init__(self, busy_user, free_user, sub, body, html, hd, start, s_id):
        self.bu = busy_user
        self.fu = free_user
        self.sub = sub
        self.start = start
        self.id = s_id
        self.creation_date = datetime.datetime.now()
        self.msg_thread = []
        self.last_body = body
        self.last_html = html
        self.last_header = hd
        self.speak_count = 0

    def add_request(self):
        self.msg_thread.append(request)
        self.last_body = request.form['text']
        self.last_html = request.form['html']
        self.last_header = sara_parseheader(request.form['headers'])

    def speak(self, string):
        # send email to free user with the given string

        new_body = string
        if (self.sub.lower()[0:3] == 're:'):
            new_sub = self.sub
        else:
            new_sub = 'Re:'+self.sub


        if self.start == 'Busy' and self.speak_count == 0:
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
        msg.set_html(new_body)
        msg.set_text(new_body)
        msg.set_from(SARA_NAME)
        msg.set_headers({"In-Reply-To": new_in_reply_to, "References": new_references})

        sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
        status, msg = sg.send(msg)

        self.speak_count += 1
        return status

    def listen(self):
    # listen to free
        # extract the new text
        new_text = EmailReplyParser.parse_reply(self.last_body)

