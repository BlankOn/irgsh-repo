import tempfile
import os
import gzip
from subprocess import Popen, PIPE, STDOUT

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
            distribution, component, task_arch_list,
            section=None, priority=None):

        version = version.split(':')[-1]

        repo_log = []
        arch = None
        try:
            # Install source
            dsc = '%s_%s.dsc' % (package, version)
            dsc_file = os.path.join(settings.INCOMING, str(spec_id), 'source', dsc)
            cmd = ['reprepro', '-VVV',
                   '-b', settings.REPO_DIR,
                   '-C', component]
            if priority is not None:
                cmd += ['-P', priority]
            if section is not None:
                cmd += ['-S', section]
            cmd += ['includedsc', distribution, dsc_file]
            self.execute_cmd(cmd, repo_log)

            # Add deb for each architecture
            for index, task_arch in enumerate(task_arch_list):
                task_id, arch = task_arch

                changes = '%s_%s_%s.changes' % (package, version, arch)
                changes_file = os.path.join(settings.INCOMING, str(spec_id), task_id, changes)

                # Install binary packages only
                files = {'.deb': [], '.udeb': []}
                c = Changes(open(changes_file))
                for info in c['Files']:
                    fname = info['name']
                    name, ext = os.path.splitext(fname)

                    # Only accept .deb and .udeb
                    if not ext in ['.deb', '.udeb']:
                        continue

                    if index == 0 or fname.endswith('_%s.deb' % arch) \
                       or fname.endswith('_%s.udeb' % arch):
                        # Only first listed architecture installs
                        # architecture independent (*_all.deb/*_all.udeb) packages
                        files[ext].append(fname)

                for ext in files:
                    action = 'includedeb'
                    if ext == '.udeb':
                        action = 'includeudeb'

                    debs = [os.path.join(settings.INCOMING, str(spec_id),
                                         task_id, deb)
                            for deb in files[ext]]
                    if len(debs) > 0:

                        cmd = 'reprepro -VVV -b %s -C %s %s %s' % \
                              (settings.REPO_DIR, component, action, distribution)
                        cmd = cmd.split() + debs
                        self.execute_cmd(cmd, repo_log)

                manager.update_status(spec_id, manager.SUCCESS, arch)

            # Report all done
            manager.update_status(spec_id, manager.COMPLETE)

        except (RepoBuildError, StandardError), e:
            self.get_logger().error('[%s] %s' % (spec_id, str(e)))
            manager.update_status(spec_id, manager.FAILURE, arch)

        finally:
            self.send_log(spec_id, repo_log)

    def execute_cmd(self, cmd, repo_log):
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        stdout, stderr = p.communicate()
        err = ''

        log = self.get_logger()
        log.debug('Executed: %s' % cmd)
        log.debug('  return: %s' % p.returncode)

        repo_log.append((cmd, p.returncode, stdout))

        if p.returncode != 0:
            raise RepoBuildError(p.returncode, err)

    def send_log(self, spec_id, repo_log):
        try:
            fd, logfile = tempfile.mkstemp('-repo-log')
            f = gzip.open(logfile, 'wb')

            for cmd, ret, log in repo_log:
                f.write('# command: %s\n' % cmd)
                f.write('# return: %s\n' % ret)
                f.write(log)
                f.write('\n\n')

            f.close()

            manager.send_log(spec_id, logfile)

        finally:
            if os.path.exists(logfile):
                os.unlink(logfile)

