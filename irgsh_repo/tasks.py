import tempfile
import os
import gzip
from subprocess import Popen, PIPE

from celery.task import Task

from irgsh_repo import manager
from irgsh_repo.conf import settings

class RepoRebuildError(Exception):
    pass

class RebuildRepo(Task):
    exchange = 'repo'
    ignore_result = True

    def run(self, spec_id, package, distribution, component,
            arch_changes_list):

        try:
            # Rebuild repo for each architecture
            for index, arch_changes in enumerate(arch_changes_list):
                arch, changes = arch_changes
                self.rebuild_repo(spec_id, arch, changes, component, distribution)

            # Report all done
            manager.update_status(spec_id, manager.COMPLETE)

        except RepoRebuildError:
            pass

    def rebuild_repo(self, spec_id, arch, changes, component, distribution):
        try:
            # Logger
            fd, fname = tempfile.mkstemp()
            f = gzip.open(fname, 'wb')

            # Build repo
            changes_file = os.path.join(settings.INCOMING, changes)
            cmd = 'reprepro -b %(base)s -C %(component)s include %(dist)s %(changes)s' % \
                  {'base': settings.REPO_DIR,
                   'component': component,
                   'dist': distribution,
                   'changes': changes_file}
            p = Popen(cmd.split(), stdout=f, stderr=f)
            p.communicate()

            if p.returncode == 0:
                manager.update_status(spec_id, manager.SUCCESS, arch)

            else:
                manager.update_status(spec_id, manager.FAILURE, arch)
                raise RepoRebuildError

        finally:
            f.close()
            self.upload_log(spec_id, arch, fname)
            os.unlink(fname)

    def upload_log(self, spec_id, arch, fname):
        manager.send_log(spec_id, fname, arch)

