#  ------------------------------------------------ #
# Build message queue of push notifications from google pub/sub.
# Started with producer-consumer model but later found out
# well-built solutions based on celery, rabbitMQ, Redis etc.
# flask + celery is a good model for asynchronous management (AQM)
# of messages, redis or rabbitMQ is a good message broker
# Using MongoDB or other NoSQL databases for queue implementation
# is not suggested instead use persistent messages in AQM
# example: http://blog.miguelgrinberg.com/post/using-celery-with-flask
#  ------------------------------------------------ #

from __future__ import absolute_import

from planus.work.celery import app


# local code
from planus.src import sara
from planus.src import google

# data stores
from pymongo import MongoClient
mclient = MongoClient() # get a client
db = mclient.sara.handles # get the database, like a table in sql
# need a shared variable among the celery workers to
# synchronize with historyID. Using database is not
# a thread-safe solution. Same issue was pointed in
# http://www.leehodgkinson.com/blog/sharing-variables-between-celery-workers/
dbh = mclient.sara.historyid


@app.task
def print_hello():
    print '***CELERY****::hello there'



# incoming POST message
# https://cloud.google.com/pubsub/subscriber
# "For the most part Pub/Sub delivers each message once, and in the order in
# which it was published. However, once-only and in-order delivery are not guaranteed:
# it may happen that a message is delivered more than once, and out of order.
# Therefore, your subscriber should be idempotent when processing messages, and,
# if necessary, able to handle messages received out of order. If ordering is
# important, we recommend that the publisher of the topic to which you subscribe
# include some kind of sequence information in the message."

@app.task
def push_message(data):

    print "-----WORKER START-----"

    gm = google.create_gmail_client()
    newHistoryID = data['historyId']


    record = dbh.find_one({'type': 'lastHistoryId'})
    if record is None:
        lastHistoryID = long(22425)
    else:
        lastHistoryID = record['historyId']

    print('Pushed History=%d, last History=%d'%(newHistoryID, lastHistoryID))

    # accept only if pushed historyID is newer
    if lastHistoryID >= newHistoryID:
        print('RETURNING: No new items')
        return

    res = dbh.update(
        {'type': 'lastHistoryId'},
        {
            'type': 'lastHistoryId',
            'historyId': newHistoryID,
        },  upsert = True
        )

    changes = google.ListHistory(gm, 'me', lastHistoryID)
    print "LEN CHANGES =%d"%len(changes)

    # pprint(changes)
    if changes == None:
        print "------NO NEW MESSAGES-----"
        return

    for history in changes:
        if 'messagesAdded' in history:
            for messages in history['messagesAdded']:

                print "------MESSAGE ADDED-----"
                message_id = messages['message']['id']
                thread_id = messages['message']['threadId']
                sara.sara_handle(message_id, thread_id)

    print "-----WORKER FINISH-----"


@app.task
def new_signup(msg_id, thread_id):

    # handles the redirection from thanks.html when a new user integrates
    # his/her calendar. Pull up the second last message_id and
    # receive(), the last message_id corresponds to sara's bcc

    record = db.find_one({'thread_id': thread_id})
    if record is None:
        sara.sara_debug('Unable to sign up')
    else:
        if len(record['mlist']) >= 2:
            sara.sara_handle(record['mlist'][-2], thread_id)
        else:
            return

