import urllib2
import urllib

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

