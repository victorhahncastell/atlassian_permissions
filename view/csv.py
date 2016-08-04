#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv, io

from . import TextView


class WorldCsvView(TextView):
    def __init__(self, my_little_atlassian_world):
        super().__init__(my_little_atlassian_world)

    def generate(self, header=True, dialect='unix'):
        output = io.StringIO()
        writer = csv.writer(output, dialect=dialect)
        if header:  # first CSV line shall contain column headers
            writer.writerow(["Product", "Project", "Permission", "Type", "Assignee"])
        for line in self.model.flat_permissions:
            writer.writerow(line)
        self._output = output.getvalue()
