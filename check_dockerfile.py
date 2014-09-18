#!/usr/bin/env python

import argparse
import re
#from json import JSONEncoder
import json

class Dockerfile(object):

    def __init__(self, dockerfile):
        self.dockerfile = dockerfile
        self.f = open(self.dockerfile, 'r')
        self._layer_count = 0
        self._from_val = ""
        self.process_dockerfile()

    def process_dockerfile(self):
        for line in self.f:
            p = re.compile(r'FROM (.+$)')
            from_line = p.match(line)
            self.incr_layer_count()
            if from_line:
                self.set_from_val(from_line.group(1))

    @property
    def from_val(self):
        return self._from_val

    def set_from_val(self, val):
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
    def layer_count(self):
        return self._layer_count

    def incr_layer_count(self):
        self._layer_count = self._layer_count + 1

    def print_summary(self):
        print self.from_val
        print "latest? %s" % self.is_latest
        print "tag? %s" % self.has_tag
        print self.layer_count

    def to_json(self):
        print json.dumps({
                "FROM": self.from_val,
                "latest": self.is_latest,
                "has_tag": self.has_tag,
                "layer_count": self.layer_count
                },
                sort_keys=True, indent=4)

def main():
    """Entrypoint for script"""
    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile", help="Dockerfile to validate")
    args = parser.parse_args()

    d = Dockerfile(args.dockerfile)
    #d.print_summary()
    d.to_json()

if __name__ == '__main__':
    main()

