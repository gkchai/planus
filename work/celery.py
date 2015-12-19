from __future__ import absolute_import

from celery import Celery

app = Celery('planus.work',
             broker='amqp://',
             backend='amqp://',
             include=['planus.work.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_ACCEPT_CONTENT = ['json', 'pickle', 'msgpack', 'yaml'],
    CELERY_TASK_SERIALIZER = 'json',
)

if __name__ == '__main__':
    app.start()