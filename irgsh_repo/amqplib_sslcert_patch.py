from amqplib.client_0_8 import transport

_use_configured_cert = False

class SSLTransportWithCert(transport.SSLTransport):
    def __init__(self, host, connect_timeout, ssl_cert=None, ssl_key=None):
        super(SSLTransportWithCert, self).__init__(host, connect_timeout)
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

    def _setup_transport(self):
        if transport.HAVE_PY26_SSL:
            import ssl
            self.sslobj = ssl.wrap_socket(self.sock,
                                          keyfile=self.ssl_key,
                                          certfile=self.ssl_cert)
            self.sslobj.do_handshake()
        else:
            import socket
            self.sslobj = socket.ssl(self.sock,
                                     keyfile=self.ssl_key,
                                     certfile=self.ssl_cert)

original_create_transport = transport.create_transport
def create_transport_with_cert(host, connect_timeout, ssl=False,
                               ssl_cert=None, ssl_key=None):
    if _use_configured_cert:
        from irgsh_repo.conf import settings
        if ssl_cert is None:
            ssl_cert = settings.SSL_CERT
        if ssl_key is None:
            ssl_key = settings.SSL_KEY
        ssl = True

    if not ssl or ssl_cert is None:
        return original_create_transport(host, connect_timeout, ssl)
    else:
        return SSLTransportWithCert(host, connect_timeout, ssl_cert, ssl_key)

transport.create_transport = create_transport_with_cert

def use_configured_cert(enabled=True):
    global _use_configured_cert
    _use_configured_cert = enabled

