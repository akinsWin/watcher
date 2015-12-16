# -*- encoding: utf-8 -*-
# Copyright (c) 2015 b<>com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

import importlib

from docutils import nodes
from docutils.parsers import rst
from docutils import statemachine as sm

from watcher.version import version_info

import textwrap


class WatcherTerm(rst.Directive):
    """Directive to import an RST formatted docstring into the Watcher glossary

    How to use it
    -------------

    # inside your .py file
    class DocumentedObject(object):
        '''My *.rst* docstring'''


    # Inside your .rst file
    .. watcher-term:: import.path.to.your.DocumentedObject

    This directive will then import the docstring and then interprete it.
    """

    # You need to put an import path as an argument for this directive to work
    required_arguments = 1

    def add_textblock(self, textblock, *lineno):
        for line in textblock.splitlines():
            self.add_line(line)

    def add_line(self, line, *lineno):
        """Append one line of generated reST to the output."""
        self.result.append(line, rst.directives.unchanged, *lineno)

    def run(self):
        self.result = sm.ViewList()

        cls_path = self.arguments[0]

        try:
            module_name, obj_name = cls_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            cls = getattr(module, obj_name)
        except Exception as exc:
            raise self.error(exc)

        self.add_class_docstring(cls)

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.result, 0, node)
        return node.children

    def add_class_docstring(self, cls):
        # Added 4 spaces to align the first line with the rest of the text
        # to be able to dedent it correctly
        cls_docstring = textwrap.dedent("%s%s" % (" " * 4, cls.__doc__))
        self.add_textblock(cls_docstring)


def setup(app):
    app.add_directive('watcher-term', WatcherTerm)
    return {'version': version_info.version_string()}
