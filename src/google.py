# import logging
# from oauth2client.client import flow_from_clientsecrets
# from oauth2client.client import FlowExchangeError
# from apiclient.discovery import build
# # ...


# # Path to client_secrets.json which should contain a JSON document such as:
# #   {
# #     "web": {
# #       "client_id": "[[YOUR_CLIENT_ID]]",
# #       "client_secret": "[[YOUR_CLIENT_SECRET]]",
# #       "redirect_uris": [],
# #       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
# #       "token_uri": "https://accounts.google.com/o/oauth2/token"
# #     }
# #   }
# CLIENTSECRETS_LOCATION = '<PATH/TO/CLIENT_SECRETS.JSON>'
# REDIRECT_URI = '<YOUR_REGISTERED_REDIRECT_URI>'
# SCOPES = [
#     'https://www.googleapis.com/auth/gmail.readonly',
#     'https://www.googleapis.com/auth/userinfo.email',
#     'https://www.googleapis.com/auth/userinfo.profile',
#     # Add other requested scopes.
# ]

# class GetCredentialsException(Exception):
#   """Error raised when an error occurred while retrieving credentials.

#   Attributes:
#     authorization_url: Authorization URL to redirect the user to in order to
#                        request offline access.
#   """

#   def __init__(self, authorization_url):
#     """Construct a GetCredentialsException."""
#     self.authorization_url = authorization_url


# class CodeExchangeException(GetCredentialsException):
#   """Error raised when a code exchange has failed."""


# class NoRefreshTokenException(GetCredentialsException):
#   """Error raised when no refresh token has been found."""


# class NoUserIdException(Exception):
#   """Error raised when no user ID could be retrieved."""


# def get_stored_credentials(user_id):
#   """Retrieved stored credentials for the provided user ID.

#   Args:
#     user_id: User's ID.
#   Returns:
#     Stored oauth2client.client.OAuth2Credentials if found, None otherwise.
#   Raises:
#     NotImplemented: This function has not been implemented.
#   """
#   # TODO: Implement this function to work with your database.
#   #       To instantiate an OAuth2Credentials instance from a Json
#   #       representation, use the oauth2client.client.Credentials.new_from_json
#   #       class method.
#   raise NotImplementedError()


# def store_credentials(user_id, credentials):
#   """Store OAuth 2.0 credentials in the application's database.

#   This function stores the provided OAuth 2.0 credentials using the user ID as
#   key.

#   Args:
#     user_id: User's ID.
#     credentials: OAuth 2.0 credentials to store.
#   Raises:
#     NotImplemented: This function has not been implemented.
#   """
#   # TODO: Implement this function to work with your database.
#   #       To retrieve a Json representation of the credentials instance, call the
#   #       credentials.to_json() method.
#   raise NotImplementedError()


# def exchange_code(authorization_code):
#   """Exchange an authorization code for OAuth 2.0 credentials.

#   Args:
#     authorization_code: Authorization code to exchange for OAuth 2.0
#                         credentials.
#   Returns:
#     oauth2client.client.OAuth2Credentials instance.
#   Raises:
#     CodeExchangeException: an error occurred.
#   """
#   flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, ' '.join(SCOPES))
#   flow.redirect_uri = REDIRECT_URI
#   try:
#     credentials = flow.step2_exchange(authorization_code)
#     return credentials
#   except FlowExchangeError, error:
#     logging.error('An error occurred: %s', error)
#     raise CodeExchangeException(None)


# def get_user_info(credentials):
#   """Send a request to the UserInfo API to retrieve the user's information.

#   Args:
#     credentials: oauth2client.client.OAuth2Credentials instance to authorize the
#                  request.
#   Returns:
#     User information as a dict.
#   """
#   user_info_service = build(
#       serviceName='oauth2', version='v2',
#       http=credentials.authorize(httplib2.Http()))
#   user_info = None
#   try:
#     user_info = user_info_service.userinfo().get().execute()
#   except errors.HttpError, e:
#     logging.error('An error occurred: %s', e)
#   if user_info and user_info.get('id'):
#     return user_info
#   else:
#     raise NoUserIdException()


# def get_authorization_url(email_address, state):
#   """Retrieve the authorization URL.

#   Args:
#     email_address: User's e-mail address.
#     state: State for the authorization URL.
#   Returns:
#     Authorization URL to redirect the user to.
#   """
#   flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, ' '.join(SCOPES))
#   flow.params['access_type'] = 'offline'
#   flow.params['approval_prompt'] = 'force'
#   flow.params['user_id'] = email_address
#   flow.params['state'] = state
#   return flow.step1_get_authorize_url(REDIRECT_URI)


# def get_credentials(authorization_code, state):
#   """Retrieve credentials using the provided authorization code.

#   This function exchanges the authorization code for an access token and queries
#   the UserInfo API to retrieve the user's e-mail address.
#   If a refresh token has been retrieved along with an access token, it is stored
#   in the application database using the user's e-mail address as key.
#   If no refresh token has been retrieved, the function checks in the application
#   database for one and returns it if found or raises a NoRefreshTokenException
#   with the authorization URL to redirect the user to.

#   Args:
#     authorization_code: Authorization code to use to retrieve an access token.
#     state: State to set to the authorization URL in case of error.
#   Returns:
#     oauth2client.client.OAuth2Credentials instance containing an access and
#     refresh token.
#   Raises:
#     CodeExchangeError: Could not exchange the authorization code.
#     NoRefreshTokenException: No refresh token could be retrieved from the
#                              available sources.
#   """
#   email_address = ''
#   try:
#     credentials = exchange_code(authorization_code)
#     user_info = get_user_info(credentials)
#     email_address = user_info.get('email')
#     user_id = user_info.get('id')
#     if credentials.refresh_token is not None:
#       store_credentials(user_id, credentials)
#       return credentials
#     else:
#       credentials = get_stored_credentials(user_id)
#       if credentials and credentials.refresh_token is not None:
#         return credentials
#   except CodeExchangeException, error:
#     logging.error('An error occurred during code exchange.')
#     # Drive apps should try to retrieve the user and credentials for the current
#     # session.
#     # If none is available, redirect the user to the authorization URL.
#     error.authorization_url = get_authorization_url(email_address, state)
#     raise error
#   except NoUserIdException:
#     logging.error('No user ID could be retrieved.')
#   # No refresh token has been retrieved.
#   authorization_url = get_authorization_url(email_address, state)
#   raise NoRefreshTokenException(authorization_url)










# #!/usr/bin/python
# #
# # Copyright 2012 Google Inc. All Rights Reserved.
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #    http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

# import BaseHTTPServer
# import Cookie
# import httplib2
# import StringIO
# import urlparse
# import sys

# from apiclient.discovery import build
# from oauth2client.client import AccessTokenRefreshError
# from oauth2client.client import OAuth2WebServerFlow
# from oauth2client.file import Storage

# class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
#   """Child class of BaseHTTPRequestHandler that only handles GET request."""

#   # Create a flow object. This object holds the client_id, client_secret, and
#   # scope. It assists with OAuth 2.0 steps to get user authorization and
#   # credentials. For this example, the client ID and secret are command-line
#   # arguments.

#   CLIENTSECRETS_LOCATION = 'CLIENT_SECRETS.JSON'
#   REDIRECT_URI = 'http://127.0.0.1:5000/login/google/'
#   SCOPES = [
#       # 'https://www.googleapis.com/auth/gmail.readonly',
#       # 'https://www.googleapis.com/auth/userinfo.email',
#       # 'https://www.googleapis.com/auth/userinfo.profile',
#       'https://www.googleapis.com/auth/calendar',
#   ]


#   # flow = OAuth2WebServerFlow(sys.argv[1],
#   #                            sys.argv[2],
#   #                            'https://www.googleapis.com/auth/calendar',
#   #                            redirect_uri='http://127.0.0.1:5000/')

#   flow = flow_from_clientsecrets(CLIENTSECRETS_LOCATION, ' '.join(SCOPES))
#   flow.redirect_uri = REDIRECT_URI


#   def do_GET(self):
#     """Handler for GET request."""
#     print '\nNEW REQUEST, Path: %s' % (self.path)
#     print 'Headers: %s' % self.headers

#     # To use this server, you first visit
#     # http://127.0.0.1:5000/?new_user=<some_user_name>. You can use any name you
#     # like for the new_user. It's only used as a key to store credentials,
#     # and has no relationship with real user names. In a real system, you would
#     # only use logged-in users for your system.
#     if self.path.startswith('/?new_user='):
#       # Initial page entered by user
#       self.handle_initial_url()

#     # When you redirect to the authorization server below, it redirects back
#     # to to http://127.0.0.1:5000/?code=<some_code> after the user grants access
#     # permission for your application.
#     elif self.path.startswith('/login/google/?code='):
#       # Page redirected back from auth server
#       self.handle_redirected_url()
#     # Only the two URL patterns above are accepted by this server.
#     else:
#       # Either an error from auth server or bad user entered URL.
#       self.respond_ignore()

#   def handle_initial_url(self):
#     """Handles the initial path."""
#     # The fake user name should be in the URL query parameters.
#     new_user = self.get_new_user_from_url_param()

#     # Call a helper function defined below to get the credentials for this user.
#     credentials = self.get_credentials(new_user)

#     # If there are no credentials for this fake user or they are invalid,
#     # we need to get new credentials.
#     if credentials is None or credentials.invalid:
#       # Call a helper function defined below to respond to this GET request
#       # with a response that redirects the browser to the authorization server.
#       self.respond_redirect_to_auth_server(new_user)
#     else:
#       try:
#         # Call a helper function defined below to get calendar data for this
#         # user.
#         calendar_output = self.get_calendar_data(credentials)

#         # Call a helper function defined below which responds to this
#         # GET request with data from the calendar.
#         self.respond_calendar_data(calendar_output)
#       except AccessTokenRefreshError:
#         # This may happen when access tokens expire. Redirect the browser to
#         # the authorization server
#         self.respond_redirect_to_auth_server(new_user)

#   def handle_redirected_url(self):
#     """Handles the redirection back from the authorization server."""
#     # The server should have responded with a "code" URL query parameter. This
#     # is needed to acquire credentials.
#     code = self.get_code_from_url_param()

#     # Before we redirected to the authorization server, we set a cookie to save
#     # the fake user for retrieval when handling the redirection back to this
#     # server. This is only needed because we are using this fake user
#     # name as a key to access credentials.
#     new_user = self.get_new_user_from_cookie()

#     #
#     # This is an important step.
#     #
#     # We take the code provided by the authorization server and pass it to the
#     # flow.step2_exchange() function. This function contacts the authorization
#     # server and exchanges the "code" for credentials.
#     credentials = RequestHandler.flow.step2_exchange(code)

#     # Call a helper function defined below to save these credentials.
#     self.save_credentials(new_user, credentials)

#     # Call a helper function defined below to get calendar data for this user.
#     calendar_output = self.get_calendar_data(credentials)

#     # Call a helper function defined below which responds to this GET request
#     # with data from the calendar.
#     self.respond_calendar_data(calendar_output)

#   def respond_redirect_to_auth_server(self, new_user):
#     """Respond to the current request by redirecting to the auth server."""
#     #
#     # This is an important step.
#     #
#     # We use the flow object to get an authorization server URL that we should
#     # redirect the browser to. We also supply the function with a redirect_uri.
#     # When the auth server has finished requesting access, it redirects
#     # back to this address. Here is pseudocode describing what the auth server
#     # does:
#     #   if (user has already granted access):
#     #     Do not ask the user again.
#     #     Redirect back to redirect_uri with an authorization code.
#     #   else:
#     #     Ask the user to grant your app access to the scope and service.
#     #     if (the user accepts):
#     #       Redirect back to redirect_uri with an authorization code.
#     #     else:
#     #       Redirect back to redirect_uri with an error code.
#     uri = RequestHandler.flow.step1_get_authorize_url()

#     # Set the necessary headers to respond with the redirect. Also set a cookie
#     # to store our new_user name. We will need this when the auth server
#     # redirects back to this server.
#     print 'Redirecting %s to %s' % (new_user, uri)
#     self.send_response(301)
#     self.send_header('Cache-Control', 'no-cache')
#     self.send_header('Location', uri)
#     self.send_header('Set-Cookie', 'new_user=%s' % new_user)
#     self.end_headers()

#   def respond_ignore(self):
#     """Responds to the current request that has an unknown path."""
#     self.send_response(200)
#     self.send_header('Content-type', 'text/plain')
#     self.send_header('Cache-Control', 'no-cache')
#     self.end_headers()
#     self.wfile.write(
#       'This path is invalid or user denied access:\n%s\n\n' % self.path)
#     self.wfile.write(
#       'User entered URL should look like: http://127.0.0.1:5000/?new_user=johndoe')

#   def respond_calendar_data(self, calendar_output):
#     """Responds to the current request by writing calendar data to stream."""
#     self.send_response(200)
#     self.send_header('Content-type', 'text/plain')
#     self.send_header('Cache-Control', 'no-cache')
#     self.end_headers()
#     self.wfile.write(calendar_output)

#   def get_calendar_data(self, credentials):
#     """Given the credentials, returns calendar data."""

#     print "get_calendar_data"

#     output = StringIO.StringIO()

#     # Now that we have credentials, calling the API is very similar to
#     # other authorized access examples.

#     # Create an httplib2.Http object to handle our HTTP requests, and authorize
#     # it using the credentials.authorize() function.
#     http = httplib2.Http()
#     http = credentials.authorize(http)

#     # The apiclient.discovery.build() function returns an instance of an API
#     # service object that can be used to make API calls.
#     # The object is constructed with methods specific to the calendar API.
#     # The arguments provided are:
#     #   name of the API ('calendar')
#     #   version of the API you are using ('v3')
#     #   authorized httplib2.Http() object that can be used for API calls
#     service = build('calendar', 'v3', http=http)

#     # The Calendar API's events().list method returns paginated results, so we
#     # have to execute the request in a paging loop. First, build the request
#     # object. The arguments provided are:
#     #   primary calendar for user
#     request = service.events().list(calendarId='primary')
#     # Loop until all pages have been processed.
#     while request != None:
#       # Get the next page.
#       response = request.execute()
#       # Accessing the response like a dict object with an 'items' key
#       # returns a list of item objects (events).
#       for event in response.get('items', []):
#         # The event object is a dict object with a 'summary' key.
#         output.write(repr(event.get('summary', 'NO SUMMARY')) + '\n')
#       # Get the next request object by passing the previous request object to
#       # the list_next method.
#       request = service.events().list_next(request, response)

#     # Return the string of calendar data.
#     return output.getvalue()

#   def get_credentials(self, new_user):
#     """Using the fake user name as a key, retrieve the credentials."""
#     storage = Storage('credentials-%s.dat' % (new_user))
#     return storage.get()

#   def save_credentials(self, new_user, credentials):
#     """Using the fake user name as a key, save the credentials."""
#     storage = Storage('credentials-%s.dat' % (new_user))
#     storage.put(credentials)


#   def get_new_user_from_url_param(self):
#     """Get the new_user query parameter from the current request."""
#     parsed = urlparse.urlparse(self.path)
#     new_user = urlparse.parse_qs(parsed.query)['new_user'][0]
#     print 'Fake user from URL: %s' % new_user
#     return new_user

#   def get_new_user_from_cookie(self):
#     """Get the new_user from cookies."""
#     cookies = Cookie.SimpleCookie()
#     cookies.load(self.headers.get('Cookie'))
#     new_user = cookies['new_user'].value
#     print 'Fake user from cookie: %s' % new_user
#     return new_user

#   def get_code_from_url_param(self):
#     """Get the code query parameter from the current request."""
#     parsed = urlparse.urlparse(self.path)
#     code = urlparse.parse_qs(parsed.query)['code'][0]
#     print 'Code from URL: %s' % code
#     return code

# def main():
#   try:
#     server = BaseHTTPServer.HTTPServer(('', 5000), RequestHandler)
#     print 'Starting server. Use Control+C to stop.'
#     server.serve_forever()
#   except KeyboardInterrupt:
#     print 'Shutting down server.'
#     server.socket.close()

# if __name__ == '__main__':
#   main()

import httplib2
import pprint
from apiclient import discovery
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
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
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

    SCOPES = ['https://www.googleapis.com/auth/pubsub']
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    gmail = discovery.build('gmail', 'v1', http=http)

    # results = gmail.users().labels().list(userId='me').execute()
    # labels = results.get('labels', [])
    # if not labels:
    #     print 'No labels found.'
    # else:
    #   print 'Labels:'
    #   for label in labels:
    #     print label['name']

    return gmail


def create_pubsub_client(http=None):
    credentials = client.GoogleCredentials.get_application_default()
    if credentials.create_scoped_required():
        credentials = credentials.create_scoped(SCOPES)
    if not http:
        http = httplib2.Http()
    credentials.authorize(http)

    pubsub =  discovery.build('pubsub', 'v1', http=http)
    return pubsub


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

