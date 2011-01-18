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

        try:
            # Rebuild repo for each architecture
            for index, task_arch in enumerate(task_arch_list):
                task_id, arch = task_arch

                changes = '%s_%s_%s.changes' % (package, version, arch)
                changes_file = os.path.join(settings.INCOMING, arch, changes)

                if index == 0:
                    # Install source
                    dsc = '%s_%s.dsc' % (package, version)
                    dsc_file = os.path.join(settings.INCOMING, arch, dsc)

                    cmd = 'reprepro -b %s -C %s includedsc %s %s' % \
                          (settings.REPO_DIR, component,
                           distribution, dsc_file)
                    self.execute(cmd.split())

                    # Install all packages
                    cmd = 'reprepro -b %s -C %s include %s %s' % \
                          (settings.REPO_DIR, component,
                           distribution, changes_file)
                    self.execute(cmd.split())

                else:
                    # Install binary packages only
                    debs = []
                    c = Changes(open(changes_file))
                    for info in c['Files']:
                        fname = info['name']
                        if fname.endswith('_%s.deb' % arch):
                            debs.append(info['name'])

                    debs = [os.path.join(settings.INCOMING, arch, deb)
                            for deb in debs]
                    cmd = 'reprepro -b %s -C %s includedeb %s' % \
                          (settings.REPO_DIR, component, distribution)
                    cmd = cmd.split() + debs
                    self.execute(cmd)

                manager.update_status(spec_id, manager.SUCCESS, arch)

            # Report all done
            manager.update_status(spec_id, manager.COMPLETE)

        except RepoBuildError:
            manager.update_status(spec_id, manager.FAILURE, arch)

    def execute(self, cmd):
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise RepoBuildError(p.returncode, err)

