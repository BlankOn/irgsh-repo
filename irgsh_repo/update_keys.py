import json
import os
import re
import shutil
import sys

def main():
    os.environ.setdefault('IRGSH_REPO_CONFIG', 'irgsh-repo.conf')
    os.environ.setdefault('CELERY_LOADER', 'irgsh_repo.loader.IrgshRepoLoader')

    from irgsh_repo.manager import get_keys
    from irgsh_repo.conf import settings

    try:
        # Create keys
        print 'Retrieveing keys..'

        data = json.loads(get_keys())
        assert data['status'] == 'ok', 'Invalid result'

        if len(data['keys']) > 1:
            print 'Got %d keys' % len(data['keys'])
        else:
            print 'Got %d key' % len(data['keys'])

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

        print 'Inserting keys into %s..' % authorized_keys

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
            print 'Making a backup of %s into %s' % (authorized_keys, backup)

            shutil.copyfile(authorized_keys, backup)

        # Write new content

        print 'Writing new content of %s..' % authorized_keys

        f = open(authorized_keys, 'w')
        f.write('\n'.join(current))
        f.close()

        print 'Done.'

    except StandardError, e:
        print 'Error: %s' % e
        sys.exit(1)

if __name__ == '__main__':
    main()

