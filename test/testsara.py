# module to test sara

SARA = [u'Sara <sara@autoscientist.com>']
BUSY_USERS = [u'Bob Busy <busybob15@gmail.com>']
# BUSY_USERS = [u'B<busybob15@gmail.com>']
FREE_USERS = [u'Tom Free <freetom15@gmail.com>', u'Jon Free <freejon15@gmail.com>']
# FREE_USERS = [u'F1<freetom15@gmail.com>', u'F2<freejon15@gmail.com>']
PASSWORD = 'autoscientist'

import smtplib, imaplib, email
import re, datetime, pdb
import string, random, time
from loremipsum import get_sentences
import sys, traceback

def test_parse_email(email_obj):
    def get_header_obj(string):
        hparser = email.Parser.HeaderParser()
        return hparser.parsestr(string)

    def get_first_text_part(msg):
        maintype = msg.get_content_maintype()
        if maintype == 'multipart':
            for part in msg.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return msg.get_payload()

    return get_header_obj(email_obj.as_string()), get_first_text_part(email_obj)

def random_body():
    return "Let's schedule a meeting at %d %s at my conference room. %s"%(random.randint(1,10), random.choice(['AM', 'PM']), ' '.join(get_sentences(2)))

def test_quote_body(msg, body):

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


def test_parse_run(seq, test_id):

    # @seq      : ordered list with elements of form: (from_addr, to_addrs,
    #             cc_addrs, reply_type) where to_addrs is a list etc.

    subject = "Let's meet ?" + " " + "[TestID: %s]"%test_id
    for idx, item in enumerate(seq):

        body = item[4]

        print "-----------------Sending Mail-----------------"
        print "From: ", ','.join(item[0])
        print "To: ", ','.join(item[1])
        print "CC: ", (','.join(item[2]) if item[2] else '')
        print "Subject: ", subject
        print "Body: ", body[:50]+"\n"


        if idx == 0:
            assert item[3] == 'Compose'
            test_send(item[0], item[1], item[2], subject, body, None, item[3])
        else:
            assert item[3] != 'Compose', "New email thread not supported!"
            last_email = None

            # item[0] wants to send reply-to item[1]. First find the most recent
            # mail was that sent from item[1] to item[0].
            last_recv_email =  email.Message.Message()

            print "Checking existing mail thread ...",

            while last_recv_email['Message-ID'] is None:
                time.sleep(20)
                last_recv_email = test_check_mail(item[0], item[0], "INBOX", test_id)

            print "Got Thread\n"
            print "\t From: ", last_recv_email['From']
            print "\t To: ", last_recv_email['To']
            print "\t CC: ", last_recv_email['CC']
            print "\n"

            test_send(item[0], item[1], item[2], subject, body, last_recv_email, item[3])

        print "---------------Done Sending Mail---------------\n\n"



def test_send(from_addr, to_addrs, cc_addrs, subject, new_body, last_email, reply_type):

    # @from_addr      : single-element list of RFC 822 from-address string
    # @to_addrs       : list of RFC 822 to-address strings
    # @cc_addrs       : list of RFC 822 cc-address strings
    # @subject        : subject of the email (if reply type then prefix 'Re:')
    # @new_body       : new text to be inserted
    # @last_email     : email object (instancetype = email.Message.Message)
    # @reply_type     : ['Compose', 'Reply-To', 'Reply-All']

    username = re.search(r'(?<=<)\w+',from_addr[0]).group(0)
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.ehlo()
    session.starttls()
    session.login(username, PASSWORD)

    headers = "\r\n".join(["from: " + from_addr[0],
                       "to: " + ','.join(to_addrs),
                       "mime-version: 1.0",
                       "content-type: text/plain; charset=UTF-8"])

    if cc_addrs:
        headers = headers + "\r\n" +"cc: " + ','.join(cc_addrs)
        to = to_addrs + cc_addrs
    else:
        to = to_addrs

    if last_email:
        _, last_body = test_parse_email(last_email)

    if reply_type == 'Compose':
        body = new_body
        new_sub = subject

    else:

        reply_to = last_email.get('Message-ID')
        try:
            references = last_email.get('References')
        except KeyError:
            references = ""

        if reply_type == 'Reply-To':
            assert set(last_email['From'].split(",")) <= set(to_addrs), "To: address not complete for Reply-To type mail"

        if reply_type == 'Reply-All':

            to_plus_cc = (last_email['To'] + ("," + last_email['CC'] if last_email['CC'] else '')).split(",")
            to_plus_cc_minus_self = [x for x in to_plus_cc if x != from_addr[0]]

            assert set([last_email['From']]) <= set(to_addrs) and ((set(to_plus_cc_minus_self) <= set(cc_addrs if cc_addrs else '')) if to_plus_cc_minus_self else True), "To: and CC: addresses not complete for Reply-All type mail "

        headers = headers + "\r\n" + "In-Reply-To: " + reply_to
        if references:
            headers = headers + "\r\n" + "References: " + references + " " + reply_to
        else:
            headers = headers + "\r\n" + "References: " + reply_to

        body = new_body + "\r\n\r\n" + test_quote_body(last_email, last_body)

        if len(subject) < 3:
            new_sub = 'Re:'+subject
        else:
            if (subject.lower()[0:3] == 're:'):
                new_sub = subject
            else:
                new_sub = 'Re:'+subject

    headers = headers + "\r\n" +"subject: " + new_sub

    # body_of_email can be plaintext or html!
    content = headers + "\r\n\r\n" + body

    # The required arguments are an RFC 822 from-address string, a list of RFC
    # 822 to-address strings (a bare string will be treated as a list with 1
    # address), and a message string.
    x = session.sendmail(from_addr[0], to, content)
    session.quit()



def test_check_mail(self_addr, to_addr, mailfolder, test_id):

    # return the latest mail where to_addr is either in TO or CC
    # @self_addr      : RFC 822 self-address string list
    # @to_addr        : RFC 822 to-address string list
    # @mailfolder     : Mail folder to look for mail

    M = imaplib.IMAP4_SSL('imap.gmail.com')
    username = re.search(r'(?<=<)\w+',self_addr[0]).group(0)
    M.login(username, PASSWORD)

    # rv, mailboxes = M.list()
    # Gmail's system folders are the following:INBOX
    # [Gmail]/All Mail, [Gmail]/Drafts, [Gmail]/Sent Mail,
    # [Gmail]/Spam, [Gmail]/Starred, [Gmail]/Trash

    rv, _ = M.select(mailfolder)

    if rv != 'OK':
        M.close()
        M.logout()
        return

    rv, dt = M.search(None, "ALL")
    if rv != 'OK':
      print "No messages found!"
      return

    # recent mail is fetched first
    for num in list(reversed(dt[0].split())):
      rv, data = M.fetch(num, '(RFC822)')
      if rv != 'OK':
          print "ERROR getting message", num
          return

      msg = email.message_from_string(data[0][1])
      srch = re.search("\[TestID: %s\]"%test_id, msg['Subject'])

      if srch and (set((msg['To'] + (',' + msg['CC'] if msg['CC'] else '')).split(',')) >=  set(to_addr)):
        M.close()
        M.logout()
        return msg


def main():
    test_id = ''.join([random.choice(string.ascii_letters) for _ in range(10)])

    B = [BUSY_USERS[0]]
    F1 = FREE_USERS[0]
    F2 = FREE_USERS[1]
    S = SARA

    # seq = [
    #         (B, [F1], [F2], 'Compose'),
    #         ([F1], B, None, 'Reply-To'),
    #         ([F2], B, [F1], 'Reply-All'),
    #         (B, [F2], [F1], 'Reply-ALl'),
    #         ([F2], B, [F1], 'Reply-To'),
    #         ([F1], [F2], B, 'Reply-All'),
    # ]

    # seq = [
    #         (B, [F1], None, 'Compose', random_body()),
    #         ([F1], B, None, 'Reply-All', random_body()),
    #         (B, [F1], [F2], 'Reply-To', random_body()),
    #         ([F1], B, [F2], 'Reply-To', random_body()),
    #         ([F2], [F1], [F1, B[0]], 'Reply-All', random_body()),
    # ]

    seq = [
            (B, [F1], S, 'Compose', random_body()),
            # ([F1], S,  None, 'Reply-To', '16 Jul 08:00AM works.'),
    ]

    test_parse_run(seq, test_id)


if __name__ == "__main__":

    try:
        main()
    except:
        type, value, tb = sys.exc_info()
        # traceback.print_exc()
        pdb.post_mortem(tb)