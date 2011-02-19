import tempfile
import os
import gzip
from subprocess import Popen, PIPE

from celery.task import Task

try:
    from debian.deb822 import Changes
except ImportError:
    from debian_bundle.deb822 import Changes

from irgsh_repo import manager
from irgsh_repo.conf import settings

class RepoBuildError(Exception):
    def __init__(self, code, log):
        self.code = code
        self.log = log
    def __str__(self):
        return 'Code: %s' % self.code

class RebuildRepo(Task):
    exchange = 'repo'
    ignore_result = True

    def run(self, spec_id, package, version,
            distribution, component, task_arch_list):

        arch = None
        try:
            # Install source
            dsc = '%s_%s.dsc' % (package, version)
            dsc_file = os.path.join(settings.INCOMING, str(spec_id), 'source', dsc)
            cmd = 'reprepro -b %s -C %s includedsc %s %s' % \
                  (settings.REPO_DIR, component,
                   distribution, dsc_file)
            self.execute_cmd(cmd.split())

            # Add deb for each architecture
            for index, task_arch in enumerate(task_arch_list):
                task_id, arch = task_arch

                changes = '%s_%s_%s.changes' % (package, version, arch)
                changes_file = os.path.join(settings.INCOMING, str(spec_id), task_id, changes)

                # Install binary packages only
                debs = []
                c = Changes(open(changes_file))
                for info in c['Files']:
                    fname = info['name']
                    if not (fname.endswith('.deb') or fname.endswith('.udeb')):
                        continue
                    if index == 0 or fname.endswith('_%s.deb' % arch) \
                       or fname.endswith('_%s.udeb' % arch):
                        # Only first listed architecture installs
                        # architecture independent (*_all.deb) packages
                        debs.append(info['name'])

                debs = [os.path.join(settings.INCOMING, arch, deb)
                        for deb in debs]
                if len(debs) > 0:
                    cmd = 'reprepro -b %s -C %s includedeb %s' % \
                          (settings.REPO_DIR, component, distribution)
                    cmd = cmd.split() + debs
                    self.execute_cmd(cmd)

                manager.update_status(spec_id, manager.SUCCESS, arch)

            # Report all done
            manager.update_status(spec_id, manager.COMPLETE)

        except RepoBuildError:
            manager.update_status(spec_id, manager.FAILURE, arch)

    def execute_cmd(self, cmd):
        p = Popen(cmd) #, stdout=PIPE, stderr=PIPE)
        p.communicate()
        err = ''

        if p.returncode != 0:
            raise RepoBuildError(p.returncode, err)

