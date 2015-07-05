# extract the headers to debug log.txt

import cPickle as pickle
import email

LOG_DIR = '/var/www/autos/planus/log/'

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


data = read_pickle(LOG_DIR+'/log.txt')
hparser = email.Parser.HeaderParser()
headers = hparser.parsestr(data['headers'])

for item in headers.items():
    print item

# print headers.get('In-Reply-To')
# print headers.get('Message-Id')

msg = email.message_from_string(data['text'])
for part in msg.walk():
    # each part is a either non-multipart, or another multipart message
    # that contains further parts... Message is organized like a tree
    if part.get_content_type() == 'text/plain':
        print part.get_payload() # prints the raw text

sdata = read_pickle(LOG_DIR+'/sara.log')
print sdata


