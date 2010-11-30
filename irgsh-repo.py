#!/usr/bin/env python

import ConfigParser, os
import sys 
import time
import xmlrpclib
from subprocess import Popen,PIPE
from debian_bundle.deb822 import Changes

class IrgshRepo:
    incoming = None
    install_deb_only = {}    
    def __init__(self):
        config = ConfigParser.ConfigParser()
        files = config.read(['/etc/irgsh/irgsh-repo.conf','irgsh-repo.conf'])
        try:
            server = config.get('irgsh', 'server')
        except ConfigParser.NoSectionError:
            print "No 'irgsh' section in configuration file(s):"
            sys.exit(-1)
        except ConfigParser.NoOptionError:
            print "No 'server' option in configuration file(s):"
            sys.exit(-1)
             
        try:
            self.incoming = config.get('irgsh', 'incoming')
        except ConfigParser.NoOptionError:
            print "No 'incoming' option in configuration file(s):"
            sys.exit(-1)

        try:
            self.base_dir = config.get('irgsh', 'base_dir')
        except ConfigParser.NoOptionError:
            print "No 'base_dir' option in configuration file(s):"
            sys.exit(-1)
 
        try:
            archs = config.get('irgsh', 'archs').split(" ")
        except ConfigParser.NoOptionError:
            print "No 'archs' option in configuration file(s):"
            sys.exit(-1)
 
        for arch in archs:
            try:
                install_deb_only = config.get(arch, 'install_deb_only')
                self.install_deb_only[arch] = install_deb_only
            except ConfigParser.NoOptionError:
                pass
 
        try:
            self.x = xmlrpclib.ServerProxy(server)
        except Exception as e:
            print "Unable to contact %s: %s" % (server, str(e))
            sys.exit(-1)

        while True:
            self.run()
            time.sleep(10)
 
    def run(self):
        try:
            (code, reply) = self.x.get_assignments_to_install()
            if code == -1:
                print "Error getting assignments to install: %s" % reply
            else:
                assignments = reply
                for assignment in assignments:
                    (code, reply) = self.x.get_assignment_info(assignment)
                    if code == -1:
                        raise Exception(reply)
                    info = reply
                    task_info = self.x.get_task_info(info['task'])
                    distribution = task_info['distribution']
                    dsc = os.path.basename(info['dsc'])
                    if info['state'] == "F":
                        self.x.assignment_cancel(assignment, "Repository installation is canceled as the task is failed (perhaps failed by other builders)")
                    else:
                        self.install(assignment, distribution, info['architecture'], task_info['component'], dsc, task_info['arch_independent'])

        except Exception as e:
            raise
            self.x.assignment_fail(assignment, str(e))
        
        self._uploading = False
        
    def install(self, assignment, distribution, architecture, component, changes, arch_independent):
        print "Installing %s" % changes

        changes_file = os.path.join(self.incoming, changes)
        if self.install_deb_only.has_key(architecture) and self.install_deb_only[architecture] == "True" and arch_independent == False:
            f = open(changes_file)
            c = Changes(f)
            f.close()
            success = False
            for file in c['Files']:
                deb_file = os.path.join(self.incoming, file['name'])
                if not deb_file.endswith("%s.deb" % architecture):
                    continue 
                p = Popen(["reprepro", "-b", self.base_dir, "-C", component, "includedeb", distribution, deb_file], stderr=PIPE,stdout=PIPE)
                output = p.communicate()
                if p.returncode == 0:
                    success = True
                else:
                    output = "Error installing %s: %s" % (deb_file, output)
                    self.x.assignment_fail(assignment, output)
                    success = False
                    return

            if success:
                self.x.assignment_complete(assignment)
        else:
            p = Popen(["reprepro", "-b", self.base_dir, "-C", component, "include", distribution, changes_file, ], stderr=PIPE,stdout=PIPE)
            output = p.communicate()[0]
            if p.returncode == 0:
                self.x.assignment_complete(assignment)
            else:
                output = "Error installing %s: %s" % (changes_file, output)
                self.x.assignment_fail(assignment, output)

t = IrgshRepo()
