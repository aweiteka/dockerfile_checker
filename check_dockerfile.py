#!/usr/bin/env python

import argparse
import re
import json

DOCS_URL = "https://docs.docker.com/reference/builder/"

class Dockerfile(object):

    def __init__(self, dockerfile):
        self.dockerfile = dockerfile
        self._raw_file = []
        self._layer_count = 0
        self._from_val = None
        self._maintainer = None
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

    @property
    def raw_file(self):
        return self._raw_file

    def set_raw_file(self, f):
        self._raw_file.append(f)

    @property
    def from_val(self):
        return self._from_val

    def set_from(self, val):
        self._from_val = val

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
        return info

    @property
    def warnings(self):
        warning = dict()
        if not self.has_tag:
            warning.update({"tag": {
                                "line": 1,
                                "message": "No tag is used",
                                "description": "lorem ipsum tar",
                                "reference_url": DOCS_URL + "#from"}
                            })
        if not self.has_tag:
            warning.update({"maintainer": {
                                "line": None,
                                "message": "Maintainer is not defined",
                                "description": "The MAINTAINER line is useful for identifying the author in the form of MAINTAINER Joe Smith <joe.smith@example.com>",
                                "reference_url": DOCS_URL + "#maintainer"}
                            })
        return warning

    @property
    def errors(self):
        return {"Foo": "bar", "Bee": "buzz"}

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

def main():
    """Entrypoint for script"""
    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile",
                        metavar="path/to/Dockerfile",
                        help="Dockerfile to analyze")
    args = parser.parse_args()

    d = Dockerfile(args.dockerfile)
    d.to_json()

if __name__ == '__main__':
    main()


