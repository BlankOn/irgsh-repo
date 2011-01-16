import urllib2
import urllib
import httplib

from irgsh_repo.conf import settings

class HTTPSHandler(urllib2.HTTPSHandler):
    handler_order = urllib2.HTTPSHandler.handler_order - 1

    def __init__(self, debuglevel=0, key_file=None, cert_file=None):
        urllib2.HTTPSHandler.__init__(self, debuglevel)

        class HTTPSConnection(httplib.HTTPSConnection):
            def __init__(self, *args, **kwargs):
                if key_file is not None:
                    kwargs['key_file'] = key_file
                if cert_file is not None:
                    kwargs['cert_file'] = cert_file
                httplib.HTTPSConnection.__init__(self, *args, **kwargs)

        self.HTTPSConnection = HTTPSConnection

    def https_open(self, req):
        return self.do_open(self.HTTPSConnection, req)

def send_message(url, param=None):
    from poster.encode import multipart_encode
    from poster.streaminghttp import register_openers

    # Set custom HTTPS handler, other protocols will use the defaults
    key_file = getattr(settings, 'SSL_KEY', None)
    cert_file = getattr(settings, 'SSL_CERT', None)
    handler = HTTPSHandler(key_file=key_file, cert_file=cert_file)

    opener = register_openers()
    opener.add_handler(handler)

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

