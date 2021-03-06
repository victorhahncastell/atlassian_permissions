#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jinja2

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
        permdata, metadata = self._prepare_data_for_generate()
        self._output = self.template.render(permdata=permdata, metadata=metadata)

    @staticmethod
    def format_item_added(item):
        return "<ins>" + item + "</ins>"

    @staticmethod
    def format_item_removed(item):
        return "<del>" + item + "</del>"