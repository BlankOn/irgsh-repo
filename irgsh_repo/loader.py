from celery.loaders.base import BaseLoader
from celery.datastructures import DictAttribute

class IrgshRepoLoader(BaseLoader):
    def read_configuration(self):
        from irgsh_repo.conf import settings
        self.configured = True
        return DictAttribute(settings)

    def on_worker_init(self):
        self.import_default_modules()

