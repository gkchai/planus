import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os,datetime

CRLF = "\r\n"
login = "busybob15@gmail.com"
password = "autoscientist"
attendees = ["freetom15@gmail.com",    "freejon15@gmail.com", "gkciitd@gmail.com"]
organizer = "ORGANIZER;CN=Bob Busy:mailto:busybob15@gmail.com"
fro = "Bob Busy<busybob15@gmail.com>"
# fro = 'Sara<sara@autoscientist.com>'

ddtstart = datetime.datetime.now()
dtoff = datetime.timedelta(days = 1)
dur = datetime.timedelta(hours = 1)
ddtstart = ddtstart +dtoff
dtend = ddtstart + dur
dtstamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
dtstart = ddtstart.strftime("%Y%m%dT%H%M%SZ")
dtend = dtend.strftime("%Y%m%dT%H%M%SZ")

description = "DESCRIPTION: test invitation from pyICSParser"+CRLF
attendee = ""
for att in attendees:
    attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE"+CRLF+" ;CN="+att+";X-NUM-GUESTS=0:mailto:"+att+CRLF

ical = "BEGIN:VCALENDAR"+CRLF+"PRODID:pyICSParser"+CRLF+"VERSION:2.0"+CRLF+"CALSCALE:GREGORIAN"+CRLF
ical+="METHOD:REQUEST"+CRLF+"BEGIN:VEVENT"+CRLF+"DTSTART:"+dtstart+CRLF+"DTEND:"+dtend+CRLF+"DTSTAMP:"+dtstamp+CRLF+organizer+CRLF
ical+= "UID:FIXMEUID"+dtstamp+CRLF
ical+= attendee+"CREATED:"+dtstamp+CRLF+description+"LAST-MODIFIED:"+dtstamp+CRLF+"LOCATION:"+CRLF+"SEQUENCE:0"+CRLF+"STATUS:CONFIRMED"+CRLF
ical+= "SUMMARY:test "+ddtstart.strftime("%Y%m%d @ %H:%M")+CRLF+"TRANSP:OPAQUE"+CRLF+"END:VEVENT"+CRLF+"END:VCALENDAR"+CRLF

eml_body = "Email body visible in the invite of outlook and outlook.com but not google calendar"
eml_body_bin = "This is the email body in binary - two steps"
msg = MIMEMultipart('mixed')
msg['Reply-To']=fro
msg['Date'] = formatdate(localtime=True)
msg['Subject'] = "Meeting invite"+dtstart
msg['From'] = fro
msg['To'] = ",".join(attendees)

msgAlternative = MIMEMultipart('alternative')
msg.attach(msgAlternative)

part_email = MIMEText(eml_body,"html")
part_cal = MIMEText(ical,"calendar; method = REQUEST")

ical_atch = MIMEBase('application', 'ics',  name="%s"%("invite.ics"))
ical_atch.set_payload(ical)
Encoders.encode_base64(ical_atch)
ical_atch.add_header('Content-Disposition', 'attachment', filename="%s"%("invite.ics"))
msg.attach(ical_atch)

# eml_atch = MIMEBase('text/plain','')
# Encoders.encode_base64(eml_atch)
# eml_atch.add_header('Content-Transfer-Encoding', "")
# msg.attach(eml_atch)


msgAlternative.attach(part_email)
msgAlternative.attach(part_cal)

mailServer = smtplib.SMTP('smtp.gmail.com', 587)
mailServer.ehlo()
mailServer.starttls()
mailServer.ehlo()
mailServer.login(login, password)
mailServer.sendmail(fro, attendees, msg.as_string())
mailServer.close()

### send using sendgrid

from smtpapi import SMTPAPIHeader
import sendgrid

sg = sendgrid.SendGridClient('as89281446', 'krishnagitaG0')
eobj = email.message_from_string(msg.as_string())


header = SMTPAPIHeader()
msg = sendgrid.Mail()
# msg.add_to(last_email['from'])
# msg.add_cc( ",".join([SARA] + [addr for addr in fulist if addr != last_email['from']]))
# msg.set_subject(last_email['subject'])
# msg.set_text("Adding Others" + "\r\n\r\n> " + sara_quote(last_email))
# msg.set_from(SARA)
msg.set_headers()
status, msg = sg.send(msg)
