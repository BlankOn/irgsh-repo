import urllib2
import json

from irgsh_repo.conf import settings
from irgsh_repo.utils import send_message

FAILURE = -1
SUCCESS = 0
COMPLETE = 1

URL_UPDATE_STATUS = '%(host)s/build/%(spec_id)s/repo/status/'
URL_PING = '%(host)s/worker/+ping/'

def update_status(spec_id, status, arch=None):
    host = settings.SERVER.rstrip('/')
    url = URL_UPDATE_STATUS % {'host': host, 'spec_id': spec_id}

    param = {'status': status}
    if arch is not None:
        param['arch'] = arch
    send_message(url, param)

def ping():
    host = settings.SERVER.rstrip('/')
    url = URL_PING % {'host': host}

    param = {}
    send_message(url, param)

