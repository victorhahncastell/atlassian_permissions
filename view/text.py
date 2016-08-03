#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pprint import pprint


class WorldTextView():
    def __init__(self, my_little_atlassian_world):
        self.model = my_little_atlassian_world

    def print(self):
        pprint(self.model.permissions)
