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
import yaml

DOCS_URL = "https://docs.docker.com/reference/builder/"

class DockerfileLine(object):

    def __init__(self, rules, line):
        self.line = line
        self.rules = rules
        #self._line_array = []
        #self._raw_file = []			    # the docker file itself
        #self._layer_count = 0			# how many layers will this dockerfile produce?
        #self._from_val = None			# is this a layered image?
        #self._maintainer = None			# is the MAINTAINER defined?
        #self._user_switched = False		# is USER instruction used?
        #self._ports_exposed = 0 		# have ports been EXPOSEd? how many?
        #self._sshd_installed = False	# shall sshd be installed in the image?

    @property
    def line_array(self):
        return self._line_array

    def append_line(self, line_num, inst, arg):
        self._line_array.append({
            "line": line_num,
            "instruction": inst,
            "argument": arg })


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

    def ignore_line(self, line):
        p = re.compile(r'%s' % self.rules.general['ignore_regex'])
        m = p.match(line)
        if m:
            return True
        else:
            return False

    def is_valid_instruction(self, instruction):
        if instruction not in self.rules.general['valid_instructions']:
            return False
        else:
            return True

    @staticmethod
    def evaluation():
        if len(self.errors > 0):
            return False
        return len(self.warnings)

class Output(object):
    """Base class for output"""

    def update(self, **kwargs):
        self._items.update(**kwargs)

    def increment_count(self):
        self._count += 1

class Summary(Output):
    """Subclass for summary section"""
    _items = {}

    def __init__(self):
        self.__line_count = 0
        self.__layer_count = 0
        self.__ignored_lines_count = 0
        self.__raw_file = []
        self.__valid_commands = []

    @property
    def line_count(self):
        return self.__line_count

    @line_count.setter
    def line_count(self,value=1):
        self.__line_count += value

    @property
    def layer_count(self):
        return self.__layer_count

    def incr_layer_count(self,value=1):
        self.__layer_count += value

    @property
    def ignored_lines_count(self):
        return self.__ignored_lines_count

    def incr_ignored_lines_count(self,value=1):
        self.__ignored_lines_count += value

    @property
    def items(self):
        return self._items

    @property
    def raw_file(self):
        return self.__raw_file

    @raw_file.setter
    def raw_file(self, line):
        self.__raw_file.append(line)

    @property
    def valid_commands(self):
        return self.__valid_commands

    @valid_commands.setter
    def valid_commands(self, line):
        self.__valid_commands.append(line)

class Info(Output):
    """Subclass for info section"""
    _items = {}
    _info = []
    _count = 0

    @property
    def items(self):
        return self._items

    @property
    def count(self):
        return self._count

    def incr_count(self,value=1):
        self._count += value

    def append(self, **kwargs):
        self._info.append(kwargs)

    @property
    def info(self):
        return self._info

class Warn(Output):
    """Subclass for warnings section"""
    _items = {}
    _warnings = []
    _count = 0

    #def __init__(self):
    #    self.__count = 0

    @property
    def items(self):
        return self._items

    @property
    def count(self):
        return self._count

    def incr_count(self,value=1):
        self._count += value

    def append(self, **kwargs):
        self._warnings.append(kwargs)

    @property
    def warnings(self):
        return self._warnings

class Error(Output):
    """Subclass for errors section"""
    _items = {}
    _errors = []
    _count = 0

    @property
    def items(self):
        return self._items

    @property
    def count(self):
        return self._count

    def append(self, **kwargs):
        self._errors.append(kwargs)

    @property
    def errors(self):
        return self._errors

class Rules:
    """Convert yaml into object"""
    def __init__(self, **rules):
        self.__dict__.update(rules)

def parse_rules(rules):
    f = open(rules)
    rules = yaml.safe_load(f)
    f.close()
    return Rules(**rules)

def main():
    """Entrypoint for script"""

    parser = argparse.ArgumentParser()
    parser.add_argument("dockerfile",
                        metavar="path/to/Dockerfile",
                        help="Dockerfile to analyze")
    parser.add_argument("-r", "--rules",
                       dest="rules",
                       metavar="path/to/dockerfile/rules.yaml",
                       default="dockerfile_rules.yaml",
                       help="Custom rules file. Default is dockerfile_rules.yaml")
    args = parser.parse_args()


    def match_rule(instruction_rules, arg):
        for rule in instruction_rules:
            p = re.compile(r'%s' % rule['regex'])
            m = p.search(arg)
            if m:
                rule.update({ "line": summary.line_count })
                if 'warn' in rule['level']:
                    warn.append(**rule)
                    warn.incr_count()
                elif 'error' in rule['level']:
                    error.append(**rule)
                    error.incr_count()
                elif 'info' in rule['level']:
                    info.append(**rule)
                    info.incr_count()

    def to_json():
        return json.dumps({
                "summary": summary.items,
                "info": info.items,
                "warnings": warn.items,
                "errors": error.items,
                },
                sort_keys=True, indent=4)

    def post_processing():
        for rule in rules.global_counts:
            count = 0
            for cmd in summary.valid_commands:
                if rule in cmd[0]:
                    count += 1
                #print rule, count
                #if count != rule['count']:
                #    print "ERROR %s" % cmd

    def process_dockerfile(dockerfile):
        with open(dockerfile, 'r') as f:
            for line in f:
                summary.line_count = 1
                summary.raw_file = line.strip()
                parse_dockerfile(line.strip())
        summary.update(filename = args.dockerfile)
        summary.update(raw_file_array = summary.raw_file)
        summary.update(total_lines = summary.line_count)
        summary.update(ignored_lines = summary.ignored_lines_count)
        summary.update(resulting_image_layers = summary.layer_count)
        info.update(info = info.info)
        info.update(count = info.count)
        warn.update(count = warn.count)
        warn.update(warnings = warn.warnings)
        error.update(count = error.count)
        error.update(errors = error.errors)

    def parse_dockerfile(line_text):
        dl = DockerfileLine(rules, line_text)
        if dl.ignore_line(line_text):
             summary.incr_ignored_lines_count()
             return
        else:
            p = re.compile(r'%s' % rules.general['instruction_regex'])
            m = p.match(line_text)
            if m:
                instruction, arg = (m.group(1).upper(), m.group(2))
                if dl.is_valid_instruction(instruction):
                    summary.valid_commands = (instruction, arg)
                    summary.incr_layer_count()
                    if instruction in rules.line_rules:
                        match_rule(rules.line_rules[instruction], arg)
                else:
                    error.append(
                        line = summary.line_count,
                        instruction = m.group(1),
                        arg = m.group(2),
                        text = "invalid instruction")
                    error.increment_count()

    summary = Summary()
    warn = Warn()
    info = Info()
    error = Error()

    rules = parse_rules(args.rules)
    process_dockerfile(args.dockerfile)
    post_processing()
    print to_json()

    #d.to_json()
    # -1 if errors occurred
    # number of warnings otherwise
    #return d.evaluation


if __name__ == '__main__':
    sys.exit(main())

    # stderr could be ignore as it contains some python information

