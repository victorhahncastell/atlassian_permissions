#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import jinja2

from . import TextView


class WorldHtmlView(TextView):
    def __init__(self, my_little_atlassian_world, template_filename='world_template.html.j2', template_dir=None):
        super().__init__(my_little_atlassian_world)

        self.environment = None
        """Jinja2 Environment (this generates the template object)"""

        self.template = None
        """Jinja2 template object"""

        self.template_filename = template_filename
        if template_dir:
            self.template_dir = template_dir
        else:
            self.template_dir = os.path.dirname(__file__)
        self.initialize_template()

    def initialize_template(self):
        loader = jinja2.FileSystemLoader(self.template_dir)
        self.environment = jinja2.Environment(loader=loader)
        self.environment.line_statement_prefix = '%%'
        self.environment.line_comment_prefix = '##'
        self.template = self.environment.get_template(self.template_filename)

    def generate(self):
        self._output = self.template.render(world=self.model)
