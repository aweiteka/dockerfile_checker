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

# FIXME: this class was trimmed down after the refactor
# not clear if still needed
class DockerfileLine(object):

    def __init__(self, rules, line):
        self.line = line
        self.rules = rules

    def ignore_line(self):
        """Check if line should be ignored"""
        p = re.compile(r'%s' % self.rules.general['ignore_regex'])
        m = p.match(self.line)
        if m:
            return True
        else:
            return False

    def is_valid_instruction(self, instruction):
        """Check if instruction is valid"""
        # FIXME: use self.line instead of instruction or refactor
        if instruction not in self.rules.general['valid_instructions']:
            return False
        else:
            return True

class Output(object):
    """Base class for output"""

    def update(self, **kwargs):
        """Common method to add to items dict"""
        self._items.update(**kwargs)

    def increment_count(self):
        """Common method to increment count"""
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
        """Return count of total lines (raw)"""
        return self.__line_count

    @line_count.setter
    def line_count(self,value=1):
        """Increment raw line count"""
        self.__line_count += value

    @property
    def layer_count(self):
        """Return count of resulting image layers"""
        return self.__layer_count

    def incr_layer_count(self,value=1):
        """Increment count of resulting image layers"""
        self.__layer_count += value

    @property
    def ignored_lines_count(self):
        """Return count of ignored lines found"""
        return self.__ignored_lines_count

    def incr_ignored_lines_count(self,value=1):
        """Increment count of ignored lines"""
        self.__ignored_lines_count += value

    @property
    def items(self):
        """Items in Summary section"""
        return self._items

    @property
    def raw_file(self):
        """An array of all dockerfile lines"""
        return self.__raw_file

    @raw_file.setter
    def raw_file(self, line):
        """Append to raw_file array"""
        self.__raw_file.append(line)

    @property
    def valid_commands(self):
        """Valid commands array"""
        return self.__valid_commands

    @valid_commands.setter
    def valid_commands(self, line):
        """Append to valid commands array"""
        self.__valid_commands.append(line)

class Info(Output):
    """Subclass for info section"""
    _items = {}
    _info = []
    _count = 0

    @property
    def items(self):
        """Items in Info section"""
        return self._items

    @property
    def count(self):
        """Count of information found"""
        return self._count

    def incr_count(self,value=1):
        """Increment count property"""
        self._count += value

    def append(self, **kwargs):
        """Append info to array"""
        self._info.append(kwargs)

    @property
    def info(self):
        """An array of information found"""
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
        """Items in Warn section"""
        return self._items

    @property
    def count(self):
        """Count of warnings found"""
        return self._count

    def incr_count(self,value=1):
        """Increment warnings found"""
        self._count += value

    def append(self, **kwargs):
        """Append warnings to array"""
        self._warnings.append(kwargs)

    @property
    def warnings(self):
        """An array of the actual warnings found"""
        return self._warnings

class Error(Output):
    """Subclass for errors section"""
    _items = {}
    _errors = []
    _count = 0

    @property
    def items(self):
        """Items in Error section"""
        return self._items

    @property
    def count(self):
        """count of errors found"""
        return self._count

    def append(self, **kwargs):
        self._errors.append(kwargs)

    @property
    def errors(self):
        """An array of the actual errors found"""
        return self._errors

class Rules:
    """Convert yaml into object

    Only converts first level"""
    def __init__(self, **rules):
        self.__dict__.update(rules)

def parse_rules(rules):
    """Return rule yaml file as object"""
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
        """Match lines to defined instruction rules"""
        for rule in instruction_rules:
            p = re.compile(r'%s' % rule['regex'])
            m = p.search(arg)
            if m:
                rule.update({ "line": summary.line_count })
                # TODO: duplicate code; create function
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
        """Return json format"""
        return json.dumps({
                "summary": summary.items,
                "info": info.items,
                "warnings": warn.items,
                "errors": error.items,
                },
                sort_keys=True, indent=4)

    def post_processing():
        """Check whole file against rules

        What was not provided? Multiple instructions, etc"""
        counts = [r['instruction'] for r in rules.global_counts for i in summary.valid_commands if r['instruction'] in i[0]]
        for rule in rules.global_counts:
            if counts.count(rule['instruction']) != rule['count']:
                # TODO: duplicate code; create function
                if 'warn' in rule['level']:
                    warn.append(**rule)
                    warn.incr_count()
                elif 'error' in rule['level']:
                    error.append(**rule)
                    error.incr_count()
                elif 'info' in rule['level']:
                    info.append(**rule)
                    info.incr_count()

    def process_dockerfile(dockerfile):
        """Main loop through file"""
        with open(dockerfile, 'r') as f:
            for line in f:
                summary.line_count = 1
                summary.raw_file = line.strip()
                parse_dockerfile(line.strip())
        # FIXME: put this logic into Output class
        # there must be an elegant way to do this
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
        """Parse each line of file"""
        dl = DockerfileLine(rules, line_text)
        if dl.ignore_line():
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

    # FIXME: not sure where this belongs after the refactor
    #@staticmethod
    #def evaluation():
    #    if len(self.errors > 0):
    #        return False
    #    return len(self.warnings)

    summary = Summary()
    warn = Warn()
    info = Info()
    error = Error()

    rules = parse_rules(args.rules)
    process_dockerfile(args.dockerfile)
    post_processing()
    # FIXME: we should be serializing Output object
    print to_json()

    # -1 if errors occurred
    # number of warnings otherwise
    #return d.evaluation


if __name__ == '__main__':
    sys.exit(main())

    # stderr could be ignore as it contains some python information

