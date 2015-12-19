import httplib2
import pprint
from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
import oauth2client
import pdb
import os

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """


    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    CLIENT_SECRET_FILE = '/var/www/secrets/sara_secret.json'
    APPLICATION_NAME = 'sara_gmail'
    try:
        import argparse
        # flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    home_dir = os.path.expanduser('/var/www/secrets')
    credential_dir = os.path.join(home_dir, 'credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sara_gmail.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        #flags = --noauth_local_webserver
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials


def create_gmail_client():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    gmail = discovery.build('gmail', 'v1', http=http)
    # import pickle
    # a = pickle.dumps(gmail.__getstate__())
    # return a
    return gmail


def ListHistory(service, user_id, start_history_id='1'):
  """List History of all changes to the user's mailbox.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    start_history_id: Only return Histories at or after start_history_id.

  Returns:
    A list of mailbox changes that occurred after the start_history_id.
  """
  try:
    history = (service.users().history().list(userId=user_id,
                                              startHistoryId=start_history_id)
               .execute())
    changes = history['history'] if 'history' in history else []
    while 'nextPageToken' in history:
      page_token = history['nextPageToken']
      history = (service.users().history().list(userId=user_id,
                                        startHistoryId=start_history_id,
                                        pageToken=page_token).execute())
      changes.extend(history['history'])

    return changes
  except errors.HttpError, error:
    print 'An error occurred: %s' % error


#=====================================#
# Google message resource format:
# {
#   "id": string,
#   "threadId": string,
#   "labelIds": [
#     string
#   ],
#   "snippet": string,
#   "historyId": unsigned long,
#   "internalDate": long,
#   "payload": {
#     "partId": string,
#     "mimeType": string,
#     "filename": string,
#     "headers": [
#       {
#         "name": string,
#         "value": string
#       }
#     ],
#     "body": users.messages.attachments Resource,
#     "parts": [
#       (MessagePart)
#     ]
#   },
#   "sizeEstimate": integer,
#   "raw": bytes
# }
#=====================================#



def create_pubsub_client(http=None):

    SCOPES = ['https://www.googleapis.com/auth/pubsub']

    credentials = client.GoogleCredentials.get_application_default()
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(SCOPES)
    if not http:
        http = httplib2.Http()
    credentials.authorize(http)

    pubsub =  discovery.build('pubsub', 'v1', http=http)
    return pubsub




"""Send an email message from the user's account.
"""

import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os

from apiclient import errors


def SendMessage(service, user_id, message, thread_id=None):
  """Send an email message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.

  Returns:
    Sent Message.
  """
  try:
    message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())

    print 'Message Id: %s' % message['id']
    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error


def CreateMessage(sender, to, cc, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64 encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['cc'] = cc
  message['from'] = sender
  message['subject'] = subject
  return {'raw': base64.b64encode(message.as_string())}


def CreateMessageWithAttachment(sender, to, cc, subject, message_text, file_dir,
                                filename):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.
    file_dir: The directory containing the file to be attached.
    filename: The name of the file to be attached.

  Returns:
    An object containing a base64 encoded email object.
  """
  message = MIMEMultipart()
  message['to'] = to
  message['cc'] = cc
  message['from'] = sender
  message['subject'] = subject

  msg = MIMEText(message_text)
  message.attach(msg)

  path = os.path.join(file_dir, filename)
  content_type, encoding = mimetypes.guess_type(path)

  if content_type is None or encoding is not None:
    content_type = 'application/octet-stream'
  main_type, sub_type = content_type.split('/', 1)
  if main_type == 'text':
    fp = open(path, 'rb')
    msg = MIMEText(fp.read(), _subtype=sub_type)
    fp.close()
  elif main_type == 'image':
    fp = open(path, 'rb')
    msg = MIMEImage(fp.read(), _subtype=sub_type)
    fp.close()
  elif main_type == 'audio':
    fp = open(path, 'rb')
    msg = MIMEAudio(fp.read(), _subtype=sub_type)
    fp.close()
  else:
    fp = open(path, 'rb')
    msg = MIMEBase(main_type, sub_type)
    msg.set_payload(fp.read())
    fp.close()

  msg.add_header('Content-Disposition', 'attachment', filename=filename)
  message.attach(msg)

  return {'raw': base64.b64encode(message.as_string())}

"""Get Message with given ID.
"""

import base64
import email
from apiclient import errors

def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()

    print 'Message snippet: %s' % message['snippet']

    return message
  except errors.HttpError, error:
    print 'An error occurred: %s' % error


def GetMimeMessage(service, user_id, msg_id):
  """Get a Message and use it to create a MIME Message.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A MIME Message, consisting of data from Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    print 'Message snippet: %s' % message['snippet']

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mime_msg = email.message_from_string(msg_str)

    return mime_msg
  except errors.HttpError, error:
    print 'An error occurred: %s' % error


def send_invite(service, to_addrs, location, ddtstart, ddtend):

  attendees = []
  for addr in to_addrs:
    attendees.append( {'email': addr})

  event = {
    'summary': 'Meet @ %s'%location,
    'location': location,
    'description': 'Meeting',
    'start': {
      'dateTime': ddtstart.isoformat('T'),
      # 'timeZone': 'America/Los_Angeles',
    },
    'end': {
      'dateTime': ddtend.isoformat('T'),
      # 'timeZone': 'America/Los_Angeles',
    },
    # 'recurrence': [
    #   'RRULE:FREQ=DAILY;COUNT=2'
    # ],
    'attendees': attendees,
    'reminders': {
      'useDefault': True,
      # 'overrides': [
      #   {'method': 'email', 'minutes': 24 * 60},
      #   {'method': 'popup', 'minutes': 10},
      # ],
    },
  }

  event = service.events().insert(calendarId='primary', body=event, sendNotifications=True).execute()
  print 'Event created: %s' % (event.get('htmlLink'))


def google_hande(lastHistoryID):
    pass


def main():
  pubsub = create_pubsub_client()
  gmail = create_gmail_client()

  topic = 'projects/self-1031/topics/inbox'
  policy = {
    'policy': {
      'bindings': [{
        'role': 'roles/pubsub.publisher',
        'members': ['serviceAccount:gmail-api-push@system.gserviceaccount.com'],
      }],
    }
  }
  resp = pubsub.projects().topics().setIamPolicy(resource=topic, body=policy).execute()
  next_page_token = None
  while True:
    resp = pubsub.projects().topics().list(
        project='projects/self-1031',
        pageToken=next_page_token).execute()
    # Process each topic
    for topic in resp['topics']:
        print topic['name']
    next_page_token = resp.get('nextPageToken')
    if not next_page_token:
        break

  request = {
    'labelIds': ['INBOX'],
    'topicName': 'projects/self-1031/topics/inbox'
  }
  return gmail.users().watch(userId='me', body=request).execute()


if __name__ == '__main__':
    main()

