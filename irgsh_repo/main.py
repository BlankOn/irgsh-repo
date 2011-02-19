import os

def main():
    os.environ.setdefault('IRGSH_REPO_CONFIG', 'irgsh-repo.conf')
    os.environ.setdefault('CELERY_LOADER', 'irgsh_repo.loader.IrgshRepoLoader')

    import socket
    from celery.bin import celeryd
    from celery.bin.celeryd import multiprocessing
    from irgsh_repo.conf import settings

    class WorkerCommand(celeryd.WorkerCommand):
        def get_options(self):
            opts = super(WorkerCommand, self).get_options()
            for opt in opts:
                if opt.dest == 'hostname':
                    opt.default = '%s.repo' % socket.gethostname()
            return opts

    multiprocessing.freeze_support()
    worker = WorkerCommand()
    worker.execute_from_commandline()

if __name__ == '__main__':
    main()

