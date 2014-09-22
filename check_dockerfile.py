#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    dockerfile_checker.py a sanity checker for Dockerfiles
#    Copyright (C) 2014 Aaron Weitekamp, Christoph Görn
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import argparse
import re
import json

DOCS_URL = "https://docs.docker.com/reference/builder/"

class Dockerfile(object):

    def __init__(self, dockerfile):
        self.dockerfile = dockerfile
        self._raw_file = []			    # the docker file itself
        self._layer_count = 0			# how many layers will this dockerfile produce?
        self._from_val = None			# is this a layered image?
        self._maintainer = None			# is the MAINTAINER defined?
        self._user_switched = False		# is USER instruction used?
        self._ports_exposed = 0 		# have ports been EXPOSEd? how many?
        self._sshd_installed = False	# shall sshd be installed in the image?

        self.process_dockerfile()

    def process_dockerfile(self):
        with open(self.dockerfile, 'r') as f:
            for line in f:
                self.set_raw_file(line.strip())
                self.parse_dockerfile(line)

    def parse_dockerfile(self, line):
        p = re.compile(r'(\w+)\s(.+$)')
        m = p.match(line)
        if m:
            self.incr_layer_count(line)
            if "FROM" in m.group(1):
                self.set_from(m.group(2))
            if "MAINTAINER" in m.group(1):
                self.set_maintainer(m.group(2))
            if "USER" in m.group(1):
                self.set_user_switched(True)
            if "RUN" in m.group(1):
                if "ssh-server" in m.group(1) or "sshd" in m.group(1):
                    self.set_sshd_installed(True)
            if "EXPOSE" in m.group(1):
                _ports = m.group(2).split(" ")
                self.set_ports_exposed(len(_ports))

    @property
    def raw_file(self):
        return self._raw_file

    def set_raw_file(self, f):
        self._raw_file.append(f)

    @property
    def ports_exposed(self):
        return self._ports_exposed

    def set_ports_exposed(self, val):
        self._ports_exposed = val

    @property
    def from_val(self):
        return self._from_val

    def set_from(self, val):
        self._from_val = val

    @property
    def user_switched(self):
        return self._user_switched

    def set_user_switched(self, val):
        self._user_switched = val

    @property
    def sshd_installed(self):
        return self._sshd_installed

    def set_sshd_installed(self, val):
        self._sshd_installed = val

    @property
    def is_latest(self):
        if "latest" in self.from_val:
            return True
        else:
            return False

    @property
    def has_tag(self):
        if ":" in self.from_val:
            return True
        else:
            return False

    @property
    def maintainer(self):
        return self._maintainer

    def set_maintainer(self, maintainer=None):
        self._maintainer = maintainer

    @property
    def has_maintainer(self):
        if self.maintainer:
            return True
        else:
            return False

    @property
    def layer_count(self):
        return self._layer_count

    def incr_layer_count(self, line):
        if "#" not in line:
            self._layer_count = self._layer_count + 1

    @property
    def summary(self):
        return {"raw": self.raw_file,
                "FROM": self.from_val,
                "layer_count": self.layer_count
                }

    @property
    def info(self):
        info = dict()
        info.update({"Maintainer": self.maintainer})
        if self.is_latest:
            info.update({"from_latest": {
                                "line": 1,
                                "message": "base image uses 'latest' tag",
                                "description": "using the 'latest' tag may cause unpredictable builds. It is recommended that a specific tag is used in the FROM line.",
                                "reference_url": DOCS_URL + "#from"}
                        })
        if self.ports_exposed > 0:
            info.update({"ports_exposed": {
                                "line": None, # FIXME
                                "message": "a number of ports have been exposed",
                                "description": "Exposed ports may be used for linking containers or for accessing them. You should consider using the -p option with docker run.",
                                "reference_url": DOCS_URL + "#expose"}
                        })


        return info

    @property
    def warnings(self):
        warning = dict()
        if not self.has_tag:
            warning.update({"tag": {
                                "line": 1,
                                "message": "No tag is used",
                                "description": "You have not used a tag with the image used in the FROM line, this may lead to unexpected image versions used.",
                                "reference_url": DOCS_URL + "#from"}
                            })
        if not self.has_tag:
            warning.update({"maintainer": {
                                "line": None,
                                "message": "Maintainer is not defined",
                                "description": "The MAINTAINER line is useful for identifying the author in the form of MAINTAINER Joe Smith <joe.smith@example.com>",
                                "reference_url": DOCS_URL + "#maintainer"}
                            })

        if not self.user_switched:
            warning.update({"user": {
                                "line": None, # FIXME add line count
                                "message": "You have not used USER instruction, so the process(es) within the container may run as root and RUN instructions my be run as root!",
                                "reference_url": DOCS_URL + "#user"}
                            })

        if not self.sshd_installed:
            warning.update({"sshd": {
                                "line": None, # FIXME add line count
                                "message": "You seem to be installing sshd to the Docker image, if you do really REALLY require this: ok, if it is just for entering the docker container consider using nsenter.",
                                "reference_url": "https://github.com/jpetazzo/nsenter"}
                            })
        if self.ports_exposed == 0:
            warning.update({"ports_exposed": {
                                "line": None, # FIXME add line count
                                "message": "You have not exposed any ports, how will the service of the container be accessed?",
                                "reference_url": DOCS_URL+"#expose"}
                            })

        return warning

    @property
    def errors(self):
        return {}

    def to_json(self):
        print json.dumps({
                "summary": self.summary,
                "info": {
                    "count": len(self.info),
                    "data": self.info
                    },
                "warnings": {
                    "count": len(self.warnings),
                    "data": self.warnings
                    },
                "errors": {
                    "count": len(self.errors),
                    "data": self.errors
                    }
                },
                sort_keys=True, indent=4)

    @staticmethod
    def evaluation():
        if len(self.errors > 0):
            return -1
        
        return len(self.warnings)

# end of class Dockerfile

def main():
    """Entrypoint for script"""
    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile",
                        metavar="path/to/Dockerfile",
                        help="Dockerfile to analyze")
    args = parser.parse_args()

    d = Dockerfile(args.dockerfile)
    d.to_json()

    # -1 if errors occurred
    # number of warnings otherwise
    return d.evaluation

if __name__ == '__main__':
    sys.exit(main())

    # stderr could be ignore as it contains some python information

