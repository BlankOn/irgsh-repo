import os
import sys

def main():
    os.environ.setdefault('IRGSH_REPO_CONFIG', 'irgsh-repo.conf')
    os.environ.setdefault('CELERY_LOADER', 'irgsh_repo.loader.IrgshRepoLoader')

    from irgsh_repo.utils import update_authorized_keys

    try:
        print 'Updating authorized_keys file..'
        total, fname = update_authorized_keys()
        print 'Total keys: %s' % total
        print 'File updated: %s' % fname
    except StandardError, e:
        print 'Error: %s' % e
        sys.exit(1)

if __name__ == '__main__':
    main()

