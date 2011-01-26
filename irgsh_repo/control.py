from datetime import datetime, timedelta

from celery.worker.control import Panel

from . import manager

_ping_threshold = timedelta(minutes=5)
_last_ping = None

@Panel.register
def report_alive(panel):
    global _last_ping

    now = datetime.now()
    if _last_ping is None or now - _last_ping >= _ping_threshold:
        _last_ping = now
        manager.ping()

    return {'status': 'ok'}

