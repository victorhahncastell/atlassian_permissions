#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty


class TextView(metaclass=ABCMeta):
    """
    Abstract base class for views that can be represented as text.
    I.e., currently all of our views.
    """
    def __init__(self, modelclass):
        self.model = modelclass
        self._output = None

    @property
    def output(self):
        if self._output is None:
            self.generate()
        return self._output

    @abstractmethod
    def generate(self):
        pass

    def export(self, filename):
        with open(filename, 'w') as file:
            file.write(self.output)

    def print(self):
        print(self.output)
