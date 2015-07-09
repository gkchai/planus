import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import COMMASPACE, formatdate
from email import Encoders
import os,datetime
import json, requests

CRLF = "\r\n"


def send_invite(from_addr, to_addrs, location, ddtstart, ddtend):

    dtstamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    dtstart = ddtstart.strftime("%Y%m%dT%H%M%SZ")
    dtend = ddtend.strftime("%Y%m%dT%H%M%SZ")
    organizer = "ORGANIZER;CN=Sara:mailto:sara@autoscientist.com"

    description = "DESCRIPTION: Meeting Invite"+CRLF
    attendee = ""
    for att in to_addrs:
        attendee += "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;RSVP=TRUE"+CRLF+" ;CN="+att+";X-NUM-GUESTS=0:mailto:"+att+CRLF

    ical = "BEGIN:VCALENDAR"+CRLF+"PRODID:pyICSParser"+CRLF+"VERSION:2.0"+CRLF+"CALSCALE:GREGORIAN"+CRLF
    ical+="METHOD:REQUEST"+CRLF+"BEGIN:VEVENT"+CRLF+"DTSTART:"+dtstart+CRLF+"DTEND:"+dtend+CRLF+"DTSTAMP:"+dtstamp+CRLF+organizer+CRLF
    ical+= "UID:FIXMEUID"+dtstamp+CRLF
    ical+= attendee+"CREATED:"+dtstamp+CRLF+description+"LAST-MODIFIED:"+dtstamp+CRLF+"LOCATION:"+CRLF+"SEQUENCE:0"+CRLF+"STATUS:CONFIRMED"+CRLF
    ical+= "SUMMARY:Meeting @"+location+CRLF+"TRANSP:OPAQUE"+CRLF+"END:VEVENT"+CRLF+"END:VCALENDAR"+CRLF

    eml_body = "Email body visible in the invite of outlook and outlook.com but not google calendar"
    eml_body_bin = "This is the email body in binary - two steps"
    msg = MIMEMultipart('mixed')
    msg['Reply-To']=from_addr
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = "Meeting @ %s"%location
    msg['From'] = from_addr
    msg['To'] = ",".join(to_addrs)

    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)

    part_email = MIMEText(eml_body,"html")
    part_cal = MIMEText(ical,"calendar; method = REQUEST")

    ical_atch = MIMEBase('application', 'ics',  name="%s"%("invite.ics"))
    ical_atch.set_payload(ical)
    Encoders.encode_base64(ical_atch)
    ical_atch.add_header('Content-Disposition', 'attachment', filename="%s"%("invite.ics"))
    msg.attach(ical_atch)

    msgAlternative.attach(part_email)
    msgAlternative.attach(part_cal)

    mailServer = smtplib.SMTP('smtp.gmail.com', 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(login, password)
    mailServer.sendmail(fro, to_addrs, msg.as_string())
    mailServer.close()


def get_free_slots(addr):
    ddtstart = datetime.datetime.now()
    ddtend = ddtstart + datetime.timedelta(days = 60)
    request_body =  {
                  "timeMin": ddtstart.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "timeMax": ddtend.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "items": [
                    {
                      "id": addr
                    }
                  ]
                }

    headers = {'content-type': 'application/json; charset=utf-8'}
    r = requests.post("https://www.googleapis.com/calendar/v3/freeBusy?fields=calendars%2CtimeMax%2CtimeMin&key=AIzaSyA7_jvVXvsBUR85WFuMX_esU2Rgbyg0zpU", data=json.dumps(request_body), headers=headers)

    fs_st, fs_en = [ddtstart],[]
    bs = []
    for item in r.json()['calendars'][addr]['busy']:
        bts = datetime.datetime.strptime(item['start'], "%Y-%m-%dT%H:%M:%SZ")
        bte = datetime.datetime.strptime(item['end'], "%Y-%m-%dT%H:%M:%SZ")

        fs_en.append(bts - datetime.timedelta(milliseconds=0))
        fs_st.append(bte + datetime.timedelta(milliseconds=0))

        bs.append((bts,bte))

    #add last element of fs_en
    fs_en.append(ddtend)

    # merge fs_st, fs_en and pair them
    fs_obj = []
    for idx, item in enumerate(fs_st):
        if fs_en[idx] > fs_st[idx] + datetime.timedelta(seconds=1):
            fs_obj.append({
                        "start": fs_st[idx],
                        "end": fs_en[idx]
                        })
    return fs_obj

if __name__ == '__main__':

    login = "busybob15@gmail.com"
    password = "autoscientist"
    attendees = ["freetom15@gmail.com", "freejon15@gmail.com", "gkciitd@gmail.com", 'anandacontact@gmail.com']
    fro = "Bob Busy<busybob15@gmail.com>"


    fs = get_free_slots(login)
    send_invite(fro, attendees, "Starbucks", datetime.datetime.now()+datetime.timedelta(minutes=30), datetime.datetime.now()+datetime.timedelta(minutes=60))
