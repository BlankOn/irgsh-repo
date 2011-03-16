__version__ = '0.5'

def patch_amqplib():
    import sys
    import os
    if not os.environ.has_key('IRGSH_PATCHED_AMQPLIB'):
        from irgsh_repo import amqplibssl
        sys.modules['amqplib'] = amqplibssl
        os.environ['IRGSH_PATCHED_AMQPLIB'] = '1'

patch_amqplib()

