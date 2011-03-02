__version__ = '0.5'

def patch_amqplib():
    import sys
    from . import amqplibssl
    sys.modules['amqplib'] = amqplibssl

patch_amqplib()

