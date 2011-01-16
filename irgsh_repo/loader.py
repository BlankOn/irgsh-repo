from celery.loaders.base import BaseLoader

class IrgshRepoLoader(BaseLoader):
    def read_configuration(self):
        from irgsh_repo.conf import settings
        self.configured = True
        return settings

    def on_worker_init(self):
        self.import_default_modules()

