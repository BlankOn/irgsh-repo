#!/usr/bin/python

from setuptools import setup

def get_version():
    import irgsh_repo
    return irgsh_repo.__version__

packages = ['irgsh_repo', 'irgsh_repo.conf']

setup(name='irgsh-repo',
      version=get_version(),
      description='irgsh repository builder',
      url='http://irgsh.blankonlinux.or.id',
      packages=packages,
      maintainer='BlankOn Developers',
      maintainer_email='blankon-dev@googlegroups.com',
      entry_points={'console_scripts': ['irgsh-repo = irgsh_repo.main:main',
                                        'irgsh-upload-serve = irgsh_repo.serve:main',
                                        'irgsh-update-keys = irgsh_repo.update_keys:main']},
      install_requires=['setuptools', 'celery<2.2', 'amqplib', 'poster', 'sqlalchemy'],
     )

