import os
import sys
import json
import requests
from tempfile import NamedTemporaryFile
from subprocess import call

with open('/home/pi/pagerrc.json') as f:
    config = json.load(f)

pager_log_host = config.get('pager_log_host',
                            'https://william-ml-leslie.id.au/')

updates = requests.post(pager_log_host + 'pager/update', data={
    'token' : config['token']
}).json()

script_id = updates['script_id']
script_text = updates['script']

TRANSACTION_FILE = '/home/pi/script-transactions'

if os.path.isfile(TRANSACTION_FILE):
    with open(TRANSACTION_FILE) as f:
        for line in f:
            if line.strip() == script_id:
                sys.exit()

with open(TRANSACTION_FILE, 'a') as f:
    f.write(script_id + "\n")

temp_file = NamedTemporaryFile(delete=False)
temp_file.write(updates['script'])
temp_file.close()

call([sys.executable, temp_file.name])

os.remove(temp_file.name)
