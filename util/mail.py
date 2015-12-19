import random
import re
import email
import datetime


SARA = 'sara@autoscientist.com'
SARA_F = 'Sara <sara@autoscientist.com>'
address_dict = {SARA: ['Sara', SARA_F]}


def random_body():
    return "Hi! This is Sara. Let's schedule a meeting at %d %s. \n Regards,\n Sara"%(random.randint(1,10), random.choice(['AM', 'PM']))

def strip(string):

    raw = []
    for item in string.split(','):
        m = re.search("[\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}", string.lower())
        each = m.group(0)
        address_dict[each] = [string[0:m.start()-2], item]
        raw.append(each)
    return raw


def get_body(msg):
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



def quote(msg):

    body = get_body(msg)
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

