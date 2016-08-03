#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv


class WorldCsvView():
    def __init__(self, my_little_atlassian_world):
        self.model = my_little_atlassian_world

    def export_csv(self, filename, header=True):
        with open(filename, 'w', newline='') as fd:
            writer = csv.writer(fd, dialect='unix')
            if header:  # first CSV line shall contain column headers
                writer.writerow(["Product", "Project", "Permission", "Type", "Assignee"])
            for line in self.model.flat_permissions:
                writer.writerow(line)
