#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jinja2
import re
from deepdiff import DeepDiff

from . import TextView


class WorldHtmlView(TextView):
    def __init__(self, my_little_atlassian_world, diff=None, cmp=None, template_filename='world_template.html.j2', template_dir=None):
        super().__init__(my_little_atlassian_world, diff, cmp)

        self.environment = None
        """Jinja2 Environment (this generates the template object)"""

        self.template_filename = template_filename

        # self.template_dir
        """In which directory to look for Jinja2 templates. Default to the directory this Python file is in."""
        if template_dir:
            self.template_dir = template_dir
        else:
            self.template_dir = os.path.dirname(__file__)

        self.template = None
        """Jinja2 template object"""

        self.initialize_template()

    def initialize_template(self):
        loader = jinja2.FileSystemLoader(self.template_dir)
        self.environment = jinja2.Environment(loader=loader)
        self.environment.line_statement_prefix = '%%'
        self.environment.line_comment_prefix = '##'
        self.template = self.environment.get_template(self.template_filename)

    def generate(self):
        permdata = self.model.permissions
        metadata = dict()

        if self.diff == "yes" or self.diff == "only":
            olddata = self.cmp.permissions
            diff = DeepDiff(olddata, permdata)
            for item in diff['set_item_removed']:
                self.add_rem_parse(permdata, metadata, 'set_item_removed', item)
            for item in diff['set_item_added']:
                self.add_rem_parse(permdata, metadata, 'set_item_added', item)

        self._output = self.template.render(permdata=permdata, metadata=metadata)

    @classmethod
    def add_rem_parse(cls, root, metadata, operator, rawitem):
        # TODO: this whole string and eval is so ugly - make deepdiff give us references directly
        # note: root is used in eval()
        try:
            if ".users" in rawitem:
                base = re.sub('(.*\.users).*', '\\1', rawitem)
                item = re.sub('.*\.users(.*)', '\\1', rawitem).replace('[', '').replace(']', '').replace("'", '')
            elif ".groups" in rawitem:
                base = re.sub('(.*\.groups).*', '\\1', rawitem)
                item = re.sub('.*\.groups(.*)', '\\1', rawitem).replace('[', '').replace(']', '').replace("'", '')
            parentset = eval(base)
            if operator == 'set_item_added':
                parentset.remove(item)
                parentset.add("<ins>" + item + "</ins>")
            elif operator == 'set_item_removed':
                parentset.add("<del>" + item + "</del>")
        except:  # TODO specify which exception...
            cls.msg_compare_partially_unparsable(metadata)

    @classmethod
    def msg_compare_partially_unparsable(cls, metadata):
        """
        Call msg_header and write a header message telling the user
        that the provided comparison data is at least partly unparsable.
        """
        cls.msg_header(metadata, 'cmp_partially_unparsable',
                       "Compare data (partially) unparsable. " +
                       "Please ensure the old data was recorded using the same version " +
                       "of this software. Note this software can not currently display " +
                       "added, renamed or removed projects.")

    @classmethod
    def msg_header(cls, metadata, name, text):
        """
        Prepare a metadata message that the specific view should print header notice.
        """
        if 'header_messages' not in metadata:
            metadata['header_messages'] = dict()
        metadata['header_messages'][name] = text
