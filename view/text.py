#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pformat

from . import TextView


class WorldTextView(TextView):
    def __init__(self, my_little_atlassian_world):
        super().__init__(my_little_atlassian_world)

    def generate(self):
        self._output = str(self.model)
