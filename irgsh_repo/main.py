import os

def main():
    from . import amqplib_sslcert_patch
    amqplib_sslcert_patch.use_configured_cert()

    os.environ.setdefault('IRGSH_REPO_CONFIG', 'irgsh-repo.conf')
    os.environ.setdefault('CELERY_LOADER', 'irgsh_repo.loader.IrgshRepoLoader')

    from celery.bin import celeryd
    celeryd.main()

if __name__ == '__main__':
    main()

