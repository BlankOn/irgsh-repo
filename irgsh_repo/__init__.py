__version__ = '0.1'

def patch_amqplib():
    import sys
    from . import amqplibssl
    sys.modules['amqplib'] = amqplibssl

patch_amqplib()

