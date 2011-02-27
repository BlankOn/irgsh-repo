import re
import sys
import os
import getopt
from subprocess import Popen

from irgsh_repo import manager
from irgsh_repo.conf import settings

class ScpServe(object):
    def __init__(self, argv, cmd):
        self.argv = argv
        self.cmd = cmd

    def start(self):
        try:
            newcmd = self._start()
            assert newcmd is not None, 'Unable to rebuild command'

            self._exec(newcmd)
        except Exception, e:
            print >>sys.stderr, 'Error: %s' % e
            return False
        return True

    def _exec(self, cmd):
        p = Popen(cmd, shell=True)
        p.communicate()

        assert p.returncode == 0, 'Return code not zero'

    def _start(self):
        assert len(self.argv) == 3, 'Missing argument'
        client_type, identifier = self.argv[1:]

        assert client_type in ['builder', 'taskinit'], 'Unknown client type'
        if client_type == 'builder':
            return self._handle_builder(identifier)

        elif client_type == 'taskinit':
            return self._handle_taskinit(identifier)

        return None

    def _handle_builder(self, name):
        cmd = self.cmd.split()[0]

        # dput uploads files using scp and then chmods them
        assert cmd in ['scp', 'chmod'], 'Invalid command'

        if cmd == 'scp':
            task_id = self._parse_task_id(self._get_target())
            info = manager.get_task_info(task_id)

            assert info['builder'] == name, 'Invalid builder'

            spec_id = info['spec_id']
            path = os.path.join(settings.INCOMING, str(spec_id), task_id)
            if not os.path.exists(path):
                os.makedirs(path)

            return self._rewrite_scp(path)

        elif cmd == 'chmod':
            task_id, mode, files = self._parse_chmod_cmd()
            info = manager.get_task_info(task_id)

            assert info['builder'] == name, 'Invalid builder'

            spec_id = info['spec_id']
            path = os.path.join(settings.INCOMING, str(spec_id), task_id)
            if not os.path.exists(path):
                os.makedirs(path)

            return self._rewrite_chmod(mode, files, path)

    def _handle_taskinit(self, worker_id):
        cmd = self.cmd.split()[0]
        assert cmd == 'scp', 'Invalid command'

        spec_id = self._parse_spec_id(self._get_target())
        info = manager.get_spec_info(spec_id)

        path = os.path.join(settings.INCOMING, str(spec_id), 'source')
        if not os.path.exists(path):
            os.makedirs(path)

        return self._rewrite_scp(path)

    def _parse_scp(self):
        args = self.cmd.split()[1:]

        # from scp.c of openssh 5.3p1
        optlist, args = getopt.getopt(args, 'dfl:prtvBCc:i:P:q1246S:o:F:')

        return optlist, args

    def _parse_chmod_cmd(self):
        p = self.cmd.split()
        mode = p[1]
        files = p[2:]

        items = []

        # These files have to be in `incoming/[task_id]/[filename]` format
        pf = re.compile(r'^incoming/(\d+\.\d+\.\d+)/([^/]+)$')
        task_id = None
        for fname in files:
            m = pf.match(fname)
            assert m is not None, 'Invalid file name: %s' % fname

            tid, fn = m.groups()
            assert task_id is None or task_id == tid, \
                   'Different task id: %s (%s)' % (task_id, fname)
            task_id = tid

            items.append(fn)

        return task_id, mode, items

    def _rewrite_scp(self, path):
        optlist, args = self._parse_scp()

        cmd = ['scp']
        for k, v in optlist:
            cmd.append(k)
            if v != '':
                cmd.append(v)
        cmd.append(path)

        cmd = ' '.join(cmd)
        return cmd

    def _rewrite_chmod(self, mode, files, path):
        cmd = ['chmod', mode]
        for fname in files:
            cmd.append(os.path.join(path, fname))

        cmd = ' '.join(cmd)
        return cmd

    def _get_target(self):
        optlist, args = self._parse_scp()

        assert len(args) == 1, 'Unable to get target'

        return args[0]

    def _parse_task_id(self, target):
        p = re.compile(r'^incoming/(\d+\.\d+\.\d+)/?$')
        m = p.match(target)
        if m:
            return m.group(1)
        raise ValueError, 'Invalid target'

    def _parse_spec_id(self, target):
        p = re.compile(r'^incoming/(\d+)/?$')
        m = p.match(target)
        if m:
            return int(m.group(1))
        raise ValueError, 'Invalid target'

def main():
    cmd = os.environ.get('SSH_ORIGINAL_COMMAND', None)
    if cmd is None:
        print >>sys.stderr, 'Error: Missing value: SSH_ORIGINAL_COMMAND'
        sys.exit(1)

    os.chdir(os.path.expanduser('~'))

    serve = ScpServe(sys.argv, cmd)
    if not serve.start():
        sys.exit(1)

