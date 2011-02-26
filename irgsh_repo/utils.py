import urllib2
import urllib
import json
import os
import re
import shutil
import sys


from irgsh_repo.conf import settings

from poster.encode import multipart_encode
from poster.streaminghttp import StreamingHTTPHandler, StreamingHTTPRedirectHandler, \
                                 StreamingHTTPSHandler, StreamingHTTPSConnection

class HTTPSHandler(StreamingHTTPSHandler):
    def __init__(self, debuglevel=0, key_file=None, cert_file=None):
        self.key_file = key_file
        self.cert_file = cert_file
        StreamingHTTPSHandler.__init__(self, debuglevel)

    def https_open(self, req):
        key_file = self.key_file
        cert_file = self.cert_file

        class HTTPSConnection(StreamingHTTPSConnection):
            def __init__(self, *args, **kwargs):
                if key_file is not None:
                    kwargs['key_file'] = key_file
                if cert_file is not None:
                    kwargs['cert_file'] = cert_file
                StreamingHTTPSConnection.__init__(self, *args, **kwargs)

        return self.do_open(HTTPSConnection, req)

def send_message(url, param=None):
    # Use poster's HTTP and HTTPS handler with additional support
    # for client certificate
    key_file = getattr(settings, 'SSL_KEY', None)
    cert_file = getattr(settings, 'SSL_CERT', None)
    handler = HTTPSHandler(key_file=key_file, cert_file=cert_file)

    handlers = [StreamingHTTPHandler, StreamingHTTPRedirectHandler, handler]
    opener = urllib2.build_opener(*handlers)

    # Construct data and headers
    data = None
    has_file = False
    headers = {}
    if param is not None:
        has_file = any([type(value) == file for value in param.values()])
        if has_file:
            data, headers = multipart_encode(param)
        else:
            data = urllib.urlencode(param)

    # Create request
    request = urllib2.Request(url, data, headers)
    return opener.open(request).read()

def update_authorized_keys():
    from irgsh_repo.manager import get_keys

    # Create keys

    data = json.loads(get_keys())
    assert data['status'] == 'ok', 'Invalid result'

    command = settings.IRGSH_REPO_SERVE
    res = ['### IRGSH-REPO BEGIN ### DO NOT EDIT ###']
    for item in data['keys']:
        worker_type = item['type']
        name = item['name']
        key = item['key']
        res.append('command="%s %s %s" %s' % \
                   (command, worker_type, name, key))
    res.append('### IRGSH-REPO END ###')

    content = '\n'.join(res)

    # Insert into authorized_keys

    authorized_keys = os.path.expanduser(settings.AUTHORIZED_KEYS)

    dirname = os.path.dirname(authorized_keys)
    if dirname != '' and not os.path.exists(dirname):
        os.makedirs(dirname)
        os.chmod(dirname, 0700)

    current = []
    if os.path.exists(authorized_keys):
        current = open(authorized_keys).read().splitlines()

    pos = [0, 0]
    inside = False
    for index, line in enumerate(current):
        if line.startswith('### IRGSH-REPO BEGIN'):
            pos[0] = index
        elif line.startswith('### IRGSH-REPO END'):
            pos[1] = index + 1
    current[pos[0]:pos[1]] = [content]

    # Create backup

    backup = '%s.bak' % authorized_keys

    if os.path.exists(authorized_keys):
        shutil.copyfile(authorized_keys, backup)

    # Write new content

    f = open(authorized_keys, 'w')
    f.write('\n'.join(current))
    f.close()

    return len(data['keys']), authorized_keys

